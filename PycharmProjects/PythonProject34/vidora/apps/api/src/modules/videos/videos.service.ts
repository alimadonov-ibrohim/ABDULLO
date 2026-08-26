import { Injectable, NotFoundException, ForbiddenException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../../common/storage/storage.service';
import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';

@Injectable()
export class VideosService {
  constructor(
    private prisma: PrismaService,
    private storage: StorageService,
    @InjectQueue('video-processing') private videoQueue: Queue,
  ) {}

  async getVideos(query: {
    page?: number;
    limit?: number;
    category?: string;
    sortBy?: string;
    sortOrder?: string;
    channelId?: string;
  }) {
    const page = query.page || 1;
    const limit = Math.min(query.limit || 20, 50);
    const skip = (page - 1) * limit;

    const where: any = {
      status: 'READY',
      visibility: 'PUBLIC',
      isPublished: true,
      isDeleted: false,
    };

    if (query.channelId) where.channelId = query.channelId;
    if (query.category) {
      where.category = { slug: query.category };
    }

    const orderBy: any = {};
    const sortBy = query.sortBy || 'publishedAt';
    const sortOrder = query.sortOrder || 'desc';
    orderBy[sortBy] = sortOrder;

    const [videos, total] = await Promise.all([
      this.prisma.video.findMany({
        where,
        include: {
          channel: {
            select: {
              id: true,
              name: true,
              handle: true,
              avatar: true,
              isVerified: true,
              subscriberCount: true,
            },
          },
          category: {
            select: { id: true, name: true, slug: true },
          },
        },
        orderBy,
        skip,
        take: limit,
      }),
      this.prisma.video.count({ where }),
    ]);

    return {
      items: videos,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getVideoById(videoId: string) {
    const video = await this.prisma.video.findUnique({
      where: { id: videoId },
      include: {
        channel: {
          select: {
            id: true,
            name: true,
            handle: true,
            avatar: true,
            isVerified: true,
            subscriberCount: true,
          },
        },
        category: {
          select: { id: true, name: true, slug: true },
        },
        tags: {
          include: { tag: { select: { id: true, name: true, slug: true } } },
        },
        resolutions: {
          select: { id: true, quality: true, url: true, bitrate: true },
        },
      },
    });

    if (!video || video.isDeleted) {
      throw new NotFoundException('Video not found');
    }

    return video;
  }

  async getUploadUrl(userId: string, dto: { filename: string; contentType: string }) {
    const key = `videos/${userId}/${Date.now()}-${dto.filename}`;
    const url = await this.storage.getPresignedUploadUrl(key, dto.contentType, 7200);

    const video = await this.prisma.video.create({
      data: {
        title: dto.filename.replace(/\.[^/.]+$/, ''),
        status: 'UPLOADING',
        videoUrl: this.storage.getFileUrl(key),
        userId,
        channelId: (await this.prisma.channel.findFirst({
          where: { userId },
          select: { id: true },
        }))!.id,
      },
    });

    return {
      uploadUrl: url,
      key,
      videoId: video.id,
    };
  }

  async createVideo(userId: string, dto: {
    title: string;
    description?: string;
    categoryId?: string;
    tags?: string[];
    visibility?: string;
    language?: string;
  }) {
    const channel = await this.prisma.channel.findFirst({
      where: { userId },
    });
    if (!channel) throw new BadRequestException('No channel found');

    let tagConnections: any[] = [];
    if (dto.tags && dto.tags.length > 0) {
      for (const tagName of dto.tags) {
        const slug = tagName.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        const tag = await this.prisma.tag.upsert({
          where: { slug },
          update: {},
          create: { name: tagName, slug },
        });
        tagConnections.push({ tagId: tag.id });
      }
    }

    const video = await this.prisma.video.create({
      data: {
        title: dto.title,
        description: dto.description,
        categoryId: dto.categoryId,
        visibility: (dto.visibility as any) || 'PUBLIC',
        language: dto.language,
        userId,
        channelId: channel.id,
        tags: {
          create: tagConnections,
        },
      },
    });

    return video;
  }

  async updateVideo(videoId: string, userId: string, dto: {
    title?: string;
    description?: string;
    categoryId?: string;
    visibility?: string;
    language?: string;
  }) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video) throw new NotFoundException('Video not found');
    if (video.userId !== userId) throw new ForbiddenException('Not your video');

    return this.prisma.video.update({
      where: { id: videoId },
      data: dto,
    });
  }

  async deleteVideo(videoId: string, userId: string) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video) throw new NotFoundException('Video not found');
    if (video.userId !== userId) throw new ForbiddenException('Not your video');

    await this.prisma.video.update({
      where: { id: videoId },
      data: { isDeleted: true },
    });

    return { success: true };
  }

  async likeVideo(userId: string, videoId: string, isLike: boolean) {
    const existing = await this.prisma.videoLike.findUnique({
      where: { userId_videoId: { userId, videoId } },
    });

    if (existing) {
      if (existing.isLike === isLike) {
        await this.prisma.videoLike.delete({ where: { id: existing.id } });
        if (isLike) {
          await this.prisma.video.update({ where: { id: videoId }, data: { likeCount: { decrement: 1 } } });
        } else {
          await this.prisma.video.update({ where: { id: videoId }, data: { dislikeCount: { decrement: 1 } } });
        }
        return { liked: null };
      }

      await this.prisma.videoLike.update({
        where: { id: existing.id },
        data: { isLike },
      });

      if (isLike) {
        await this.prisma.video.update({
          where: { id: videoId },
          data: { likeCount: { increment: 1 }, dislikeCount: { decrement: 1 } },
        });
      } else {
        await this.prisma.video.update({
          where: { id: videoId },
          data: { likeCount: { decrement: 1 }, dislikeCount: { increment: 1 } },
        });
      }

      return { liked: isLike };
    }

    await this.prisma.videoLike.create({
      data: { userId, videoId, isLike },
    });

    if (isLike) {
      await this.prisma.video.update({ where: { id: videoId }, data: { likeCount: { increment: 1 } } });
    } else {
      await this.prisma.video.update({ where: { id: videoId }, data: { dislikeCount: { increment: 1 } } });
    }

    return { liked: isLike };
  }

  async recordView(userId: string | null, videoId: string, ip: string) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video) return;

    await this.prisma.video.update({
      where: { id: videoId },
      data: { viewCount: { increment: 1 } },
    });

    if (userId) {
      await this.prisma.videoView.create({
        data: { userId, videoId, ip },
      });

      await this.prisma.watchHistory.upsert({
        where: { userId_videoId: { userId, videoId } },
        update: { watchedAt: new Date() },
        create: { userId, videoId },
      });
    }
  }

  async publishVideo(videoId: string, userId: string) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video) throw new NotFoundException('Video not found');
    if (video.userId !== userId) throw new ForbiddenException('Not your video');

    return this.prisma.video.update({
      where: { id: videoId },
      data: {
        isPublished: true,
        publishedAt: new Date(),
      },
    });
  }

  async processVideo(videoId: string) {
    const video = await this.prisma.video.findUnique({ where: { id: videoId } });
    if (!video || !video.videoUrl) throw new BadRequestException('Video not ready for processing');

    await this.prisma.video.update({
      where: { id: videoId },
      data: { status: 'PROCESSING' },
    });

    await this.videoQueue.add('process-video', {
      videoId,
      inputUrl: video.videoUrl,
    });

    return { queued: true };
  }

  async getTrending(page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);

    const [videos, total] = await Promise.all([
      this.prisma.video.findMany({
        where: {
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
          publishedAt: { gte: weekAgo },
        },
        include: {
          channel: {
            select: {
              id: true,
              name: true,
              handle: true,
              avatar: true,
              isVerified: true,
            },
          },
        },
        orderBy: { viewCount: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.video.count({
        where: {
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
          publishedAt: { gte: weekAgo },
        },
      }),
    ]);

    return { items: videos, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async getShorts(page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [shorts, total] = await Promise.all([
      this.prisma.shorts.findMany({
        where: { status: 'READY', visibility: 'PUBLIC' },
        include: {
          channel: {
            select: {
              id: true,
              name: true,
              handle: true,
              avatar: true,
              isVerified: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.shorts.count({
        where: { status: 'READY', visibility: 'PUBLIC' },
      }),
    ]);

    return { items: shorts, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async getUserHistory(userId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [history, total] = await Promise.all([
      this.prisma.watchHistory.findMany({
        where: { userId },
        include: {
          video: {
            include: {
              channel: {
                select: { id: true, name: true, handle: true, avatar: true, isVerified: true },
              },
            },
          },
        },
        orderBy: { watchedAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.watchHistory.count({ where: { userId } }),
    ]);

    return {
      items: history.map(h => ({ ...h.video, progress: h.progress, watchedAt: h.watchedAt })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getWatchLater(userId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [items, total] = await Promise.all([
      this.prisma.watchLater.findMany({
        where: { userId },
        include: {
          video: {
            include: {
              channel: {
                select: { id: true, name: true, handle: true, avatar: true, isVerified: true },
              },
            },
          },
        },
        orderBy: { addedAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.watchLater.count({ where: { userId } }),
    ]);

    return {
      items: items.map(i => i.video),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getLikedVideos(userId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [likes, total] = await Promise.all([
      this.prisma.videoLike.findMany({
        where: { userId, isLike: true },
        include: {
          video: {
            include: {
              channel: {
                select: { id: true, name: true, handle: true, avatar: true, isVerified: true },
              },
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.videoLike.count({ where: { userId, isLike: true } }),
    ]);

    return {
      items: likes.map(l => l.video),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }
}
