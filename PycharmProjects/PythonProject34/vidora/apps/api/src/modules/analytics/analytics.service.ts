import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AnalyticsService {
  constructor(private prisma: PrismaService) {}

  async getChannelAnalytics(channelId: string, days = 28) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const videos = await this.prisma.video.findMany({
      where: { channelId, isDeleted: false },
      select: { id: true },
    });
    const videoIds = videos.map(v => v.id);

    const [analytics, channel] = await Promise.all([
      this.prisma.videoAnalytics.groupBy({
        by: ['date'],
        where: {
          videoId: { in: videoIds },
          date: { gte: startDate },
        },
        _sum: { views: true, watchTime: true, likes: true, comments: true },
        orderBy: { date: 'asc' },
      }),
      this.prisma.channel.findUnique({
        where: { id: channelId },
        select: {
          subscriberCount: true,
          videoCount: true,
          totalViews: true,
        },
      }),
    ]);

    const topVideos = await this.prisma.video.findMany({
      where: { channelId, isDeleted: false, status: 'READY' },
      select: {
        id: true, title: true, thumbnailUrl: true,
        viewCount: true, likeCount: true, commentCount: true,
      },
      orderBy: { viewCount: 'desc' },
      take: 10,
    });

    const totalViews = analytics.reduce((sum, a) => sum + (a._sum.views || 0), 0);
    const totalWatchTime = analytics.reduce((sum, a) => sum + (a._sum.watchTime || 0), 0);
    const totalLikes = analytics.reduce((sum, a) => sum + (a._sum.likes || 0), 0);
    const totalComments = analytics.reduce((sum, a) => sum + (a._sum.comments || 0), 0);

    return {
      summary: {
        totalViews: channel?.totalViews || 0,
        subscribers: channel?.subscriberCount || 0,
        totalVideos: channel?.videoCount || 0,
        periodViews: totalViews,
        periodWatchTime: totalWatchTime,
        periodLikes: totalLikes,
        periodComments: totalComments,
      },
      chartData: analytics.map(a => ({
        date: a.date,
        views: a._sum.views || 0,
        watchTime: a._sum.watchTime || 0,
        likes: a._sum.likes || 0,
        comments: a._sum.comments || 0,
      })),
      topVideos,
    };
  }

  async getVideoAnalytics(videoId: string, days = 28) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const [analytics, video] = await Promise.all([
      this.prisma.videoAnalytics.findMany({
        where: {
          videoId,
          date: { gte: startDate },
        },
        orderBy: { date: 'asc' },
      }),
      this.prisma.video.findUnique({
        where: { id: videoId },
        select: {
          viewCount: true, likeCount: true, dislikeCount: true,
          commentCount: true, duration: true,
        },
      }),
    ]);

    return {
      summary: {
        totalViews: video?.viewCount || 0,
        totalLikes: video?.likeCount || 0,
        totalDislikes: video?.dislikeCount || 0,
        totalComments: video?.commentCount || 0,
        duration: video?.duration || 0,
      },
      chartData: analytics.map(a => ({
        date: a.date,
        views: a.views,
        watchTime: a.watchTime,
        likes: a.likes,
        comments: a.comments,
      })),
    };
  }
}
