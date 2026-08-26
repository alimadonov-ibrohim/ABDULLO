import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as Minio from 'minio';

@Injectable()
export class StorageService implements OnModuleInit {
  private minioClient: Minio.Client;
  private bucket: string;
  private publicUrl: string;

  constructor(private configService: ConfigService) {
    this.bucket = this.configService.get('S3_BUCKET', 'vidora');
    this.publicUrl = this.configService.get('S3_PUBLIC_URL', 'http://localhost:9000/vidora');
  }

  onModuleInit() {
    this.minioClient = new Minio.Client({
      endPoint: this.configService.get('S3_ENDPOINT', 'http://localhost').replace('http://', '').replace('https://', ''),
      port: parseInt(this.configService.get('S3_PORT', '9000')),
      useSSL: this.configService.get('S3_ENDPOINT', '').startsWith('https'),
      accessKey: this.configService.get('S3_ACCESS_KEY', 'minioadmin'),
      secretKey: this.configService.get('S3_SECRET_KEY', 'minioadmin'),
    });
    this.ensureBucket();
  }

  private async ensureBucket() {
    const exists = await this.minioClient.bucketExists(this.bucket);
    if (!exists) {
      await this.minioClient.makeBucket(this.bucket);
      const policy = {
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { AWS: ['*'] },
          Action: ['s3:GetObject'],
          Resource: [`arn:aws:s3:::${this.bucket}/*`],
        }],
      };
      await this.minioClient.setBucketPolicy(this.bucket, JSON.stringify(policy));
    }
  }

  async getPresignedUploadUrl(key: string, contentType: string, expiresIn = 3600): Promise<string> {
    return this.minioClient.presignedPutObject(this.bucket, key, expiresIn);
  }

  async uploadFile(key: string, buffer: Buffer, contentType: string): Promise<string> {
    await this.minioClient.putObject(this.bucket, key, buffer, buffer.length, {
      'Content-Type': contentType,
    });
    return `${this.publicUrl}/${key}`;
  }

  async deleteFile(key: string): Promise<void> {
    await this.minioClient.removeObject(this.bucket, key);
  }

  getFileUrl(key: string): string {
    return `${this.publicUrl}/${key}`;
  }

  getPublicUrl(): string {
    return this.publicUrl;
  }
}
