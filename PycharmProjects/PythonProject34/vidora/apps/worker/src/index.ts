import Queue from 'bull';
import { PrismaClient } from '@prisma/client';
import * as Minio from 'minio';
import { execSync, exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const execAsync = promisify(exec);

const prisma = new PrismaClient();

const minioClient = new Minio.Client({
  endPoint: (process.env.S3_ENDPOINT || 'http://localhost').replace('http://', '').replace('https://', ''),
  port: parseInt(process.env.S3_PORT || '9000'),
  useSSL: (process.env.S3_ENDPOINT || '').startsWith('https'),
  accessKey: process.env.S3_ACCESS_KEY || 'minioadmin',
  secretKey: process.env.S3_SECRET_KEY || 'minioadmin',
});

const bucket = process.env.S3_BUCKET || 'vidora';
const publicUrl = process.env.S3_PUBLIC_URL || 'http://localhost:9000/vidora';

const videoQueue = new Queue('video-processing', {
  redis: { host: 'localhost', port: 6379 },
});

const RESOLUTIONS = [
  { label: '360p', width: 640, height: 360, bitrate: '500k' },
  { label: '480p', width: 854, height: 480, bitrate: '1000k' },
  { label: '720p', width: 1280, height: 720, bitrate: '2500k' },
  { label: '1080p', width: 1920, height: 1080, bitrate: '5000k' },
];

async function downloadFile(url: string, destPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to download: ${response.statusText}`);
  const buffer = Buffer.from(await response.arrayBuffer());
  fs.writeFileSync(destPath, buffer);
}

async function getVideoMetadata(filePath: string): Promise<{ width: number; height: number; duration: number }> {
  try {
    const result = execSync(
      `ffprobe -v quiet -print_format json -show_streams -show_format "${filePath}"`,
      { encoding: 'utf-8' }
    );
    const data = JSON.parse(result);
    const videoStream = data.streams.find((s: any) => s.codec_type === 'video');
    const duration = Math.ceil(parseFloat(data.format.duration || '0'));

    return {
      width: videoStream?.width || 0,
      height: videoStream?.height || 0,
      duration,
    };
  } catch {
    return { width: 1920, height: 1080, duration: 0 };
  }
}

async function generateThumbnail(filePath: string, outputPath: string, duration: number): Promise<void> {
  const seekTime = Math.min(Math.floor(duration / 3), 30);
  await execAsync(
    `ffmpeg -y -ss ${seekTime} -i "${filePath}" -vframes 1 -q:v 2 "${outputPath}"`
  );
}

async function processVideo(videoId: string, inputUrl: string) {
  const tmpDir = fs.mkdSync(path.join(os.tmpdir(), `vidora-${videoId}-`));

  try {
    await prisma.video.update({ where: { id: videoId }, data: { status: 'PROCESSING' } });

    const inputPath = path.join(tmpDir, 'input.mp4');
    await downloadFile(inputUrl, inputPath);

    const metadata = await getVideoMetadata(inputPath);
    const durations = metadata.duration;

    const thumbnailPath = path.join(tmpDir, 'thumbnail.jpg');
    await generateThumbnail(inputPath, thumbnailPath, durations);
    const thumbKey = `thumbnails/${videoId}/thumbnail.jpg`;
    const thumbBuffer = fs.readFileSync(thumbnailPath);
    await minioClient.putObject(bucket, thumbKey, thumbBuffer, thumbBuffer.length, { 'Content-Type': 'image/jpeg' });
    const thumbnailUrl = `${publicUrl}/${thumbKey}`;

    await prisma.video.update({
      where: { id: videoId },
      data: { thumbnailUrl, duration: durations },
    });

    const availableResolutions = RESOLUTIONS.filter(r => r.height <= metadata.height || metadata.height === 0);
    if (availableResolutions.length === 0) availableResolutions.push(RESOLUTIONS[0]);

    const hlsDir = path.join(tmpDir, 'hls');
    fs.mkdirSync(hlsDir, { recursive: true });

    for (const res of availableResolutions) {
      const resDir = path.join(hlsDir, res.label);
      fs.mkdirSync(resDir, { recursive: true });

      await execAsync(
        `ffmpeg -y -i "${inputPath}" -vf scale=${res.width}:${res.height} -c:v libx264 -b:v ${res.bitrate} -c:a aac -b:a 128k -f hls -hls_time 10 -hls_playlist_type vod "${resDir}/index.m3u8"`
      );

      const files = fs.readdirSync(resDir);
      for (const file of files) {
        const filePath = path.join(resDir, file);
        const fileBuffer = fs.readFileSync(filePath);
        const key = `hls/${videoId}/${res.label}/${file}`;
        const contentType = file.endsWith('.m3u8') ? 'application/x-mpegURL' : 'video/MP2T';
        await minioClient.putObject(bucket, key, fileBuffer, fileBuffer.length, { 'Content-Type': contentType });
      }

      const masterUrl = `${publicUrl}/hls/${videoId}/${res.label}/index.m3u8`;

      await prisma.videoResolution.create({
        data: {
          videoId,
          quality: res.label,
          url: masterUrl,
          bitrate: parseInt(res.bitrate),
        },
      });
    }

    const masterPlaylist = generateMasterPlaylist(availableResolutions, videoId);
    const masterKey = `hls/${videoId}/master.m3u8`;
    await minioClient.putObject(bucket, masterKey, Buffer.from(masterPlaylist), masterPlaylist.length, { 'Content-Type': 'application/x-mpegURL' });

    const hlsUrl = `${publicUrl}/${masterKey}`;

    await prisma.video.update({
      where: { id: videoId },
      data: { status: 'READY', hlsUrl, duration: durations },
    });

    console.log(`Video ${videoId} processed successfully`);
  } catch (error) {
    console.error(`Error processing video ${videoId}:`, error);
    await prisma.video.update({
      where: { id: videoId },
      data: { status: 'FAILED' },
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

function generateMasterPlaylist(resolutions: typeof RESOLUTIONS, videoId: string): string {
  let playlist = '#EXTM3U\n#EXT-X-VERSION:3\n\n';

  for (const res of resolutions) {
    const bandwidth = parseInt(res.bitrate) * 1000;
    playlist += `#EXT-X-STREAM-INF:BANDWIDTH=${bandwidth},RESOLUTION=${res.width}x${res.height}\n`;
    playlist += `${res.label}/index.m3u8\n`;
  }

  return playlist;
}

videoQueue.process('process-video', async (job) => {
  const { videoId, inputUrl } = job.data;
  console.log(`Processing video ${videoId}`);
  await processVideo(videoId, inputUrl);
  return { videoId, status: 'completed' };
});

videoQueue.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

videoQueue.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed:`, err);
});

console.log('Video processing worker started');

process.on('SIGTERM', async () => {
  await videoQueue.close();
  await prisma.$disconnect();
  process.exit(0);
});
