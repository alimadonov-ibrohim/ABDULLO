import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class SearchService {
  constructor(private prisma: PrismaService) {}

  async search(query: string, options: {
    type?: string;
    page?: number;
    limit?: number;
    sortBy?: string;
    dateFilter?: string;
    durationFilter?: string;
  } = {}) {
    const page = options.page || 1;
    const limit = Math.min(options.limit || 20, 50);
    const skip = (page - 1) * limit;
    const type = options.type || 'videos';

    if (type === 'videos') {
      return this.searchVideos(query, skip, limit, options);
    }
    if (type === 'channels') {
      return this.searchChannels(query, skip, limit);
    }
    if (type === 'playlists') {
      return this.searchPlaylists(query, skip, limit);
    }

    return this.searchAll(query, skip, limit, options);
  }

  private async searchVideos(query: string, skip: number, limit: number, options: any) {
    const where: any = {
      status: 'READY',
      visibility: 'PUBLIC',
      isPublished: true,
      isDeleted: false,
      OR: [
        { title: { contains: query, mode: 'insensitive' } },
        { description: { contains: query, mode: 'insensitive' } },
        { tags: { tag: { name: { contains: query, mode: 'insensitive' } } } },
        { category: { name: { contains: query, mode: 'insensitive' } } },
      ],
    };

    if (options.dateFilter) {
      const date = new Date();
      switch (options.dateFilter) {
        case 'today': date.setDate(date.getDate() - 1); break;
        case 'week': date.setDate(date.getDate() - 7); break;
        case 'month': date.setMonth(date.getMonth() - 1); break;
        case 'year': date.setFullYear(date.getFullYear() - 1); break;
      }
      where.publishedAt = { gte: date };
    }

    if (options.durationFilter) {
      switch (options.durationFilter) {
        case 'short': where.duration = { lte: 300 }; break;
        case 'medium': where.duration = { gte: 300, lte: 1200 }; break;
        case 'long': where.duration = { gte: 1200 }; break;
      }
    }

    const orderBy: any = {};
    switch (options.sortBy) {
      case 'date': orderBy.publishedAt = 'desc'; break;
      case 'views': orderBy.viewCount = 'desc'; break;
      case 'rating': orderBy.likeCount = 'desc'; break;
      default: orderBy.viewCount = 'desc'; break;
    }

    const [items, total] = await Promise.all([
      this.prisma.video.findMany({
        where,
        include: {
          channel: {
            select: { id: true, name: true, handle: true, avatar: true, isVerified: true },
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

    return { items, total, page: Math.floor(skip / limit) + 1, limit, totalPages: Math.ceil(total / limit) };
  }

  private async searchChannels(query: string, skip: number, limit: number) {
    const where = {
      OR: [
        { name: { contains: query, mode: 'insensitive' as const } },
        { handle: { contains: query, mode: 'insensitive' as const } },
        { description: { contains: query, mode: 'insensitive' as const } },
      ],
    };

    const [items, total] = await Promise.all([
      this.prisma.channel.findMany({
        where,
        orderBy: { subscriberCount: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.channel.count({ where }),
    ]);

    return { items, total, page: Math.floor(skip / limit) + 1, limit, totalPages: Math.ceil(total / limit) };
  }

  private async searchPlaylists(query: string, skip: number, limit: number) {
    const where = {
      isPublic: true,
      OR: [
        { name: { contains: query, mode: 'insensitive' as const } },
        { description: { contains: query, mode: 'insensitive' as const } },
      ],
    };

    const [items, total] = await Promise.all([
      this.prisma.playlist.findMany({
        where,
        include: {
          user: { select: { id: true, username: true } },
        },
        orderBy: { videoCount: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.playlist.count({ where }),
    ]);

    return { items, total, page: Math.floor(skip / limit) + 1, limit, totalPages: Math.ceil(total / limit) };
  }

  private async searchAll(query: string, skip: number, limit: number, options: any) {
    const [videos, channels] = await Promise.all([
      this.prisma.video.findMany({
        where: {
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
          OR: [
            { title: { contains: query, mode: 'insensitive' } },
            { description: { contains: query, mode: 'insensitive' } },
          ],
        },
        include: {
          channel: { select: { id: true, name: true, avatar: true, isVerified: true } },
        },
        orderBy: { viewCount: 'desc' },
        take: 10,
      }),
      this.prisma.channel.findMany({
        where: {
          OR: [
            { name: { contains: query, mode: 'insensitive' } },
            { handle: { contains: query, mode: 'insensitive' } },
          ],
        },
        orderBy: { subscriberCount: 'desc' },
        take: 5,
      }),
    ]);

    return { videos, channels };
  }

  async getSearchSuggestions(query: string) {
    if (!query || query.length < 2) return [];

    const [videos, channels] = await Promise.all([
      this.prisma.video.findMany({
        where: {
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
          title: { contains: query, mode: 'insensitive' },
        },
        select: { id: true, title: true },
        take: 5,
      }),
      this.prisma.channel.findMany({
        where: {
          name: { contains: query, mode: 'insensitive' },
        },
        select: { id: true, name: true, handle: true },
        take: 3,
      }),
    ]);

    return { videos, channels };
  }

  async saveSearchHistory(userId: string, query: string) {
    return this.prisma.searchHistory.create({
      data: { userId, query },
    });
  }

  async getSearchHistory(userId: string) {
    return this.prisma.searchHistory.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 20,
      distinct: ['query'],
    });
  }
}
