import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class RecommendationsService {
  constructor(private prisma: PrismaService) {}

  async getHomeRecommendations(userId?: string, limit = 20) {
    if (userId) {
      return this.getPersonalizedRecommendations(userId, limit);
    }
    return this.getPopularVideos(limit);
  }

  async getVideoRecommendations(videoId: string, userId?: string, limit = 20) {
    const video = await this.prisma.video.findUnique({
      where: { id: videoId },
      select: { categoryId: true, channelId: true, tags: { select: { tagId: true } } },
    });

    if (!video) return { items: [] };

    const tagIds = video.tags.map(t => t.tagId);

    const recommendations = await this.prisma.video.findMany({
      where: {
        id: { not: videoId },
        status: 'READY',
        visibility: 'PUBLIC',
        isPublished: true,
        isDeleted: false,
        OR: [
          { categoryId: video.categoryId },
          { channelId: video.channelId },
          { tags: { some: { tagId: { in: tagIds } } } },
        ],
      },
      include: {
        channel: {
          select: { id: true, name: true, handle: true, avatar: true, isVerified: true, subscriberCount: true },
        },
      },
      take: limit,
    });

    const scored = recommendations.map(r => ({
      ...r,
      score: this.calculateScore(r, video.channelId, tagIds),
    }));

    scored.sort((a, b) => b.score - a.score);

    return { items: scored.slice(0, limit) };
  }

  private async getPersonalizedRecommendations(userId: string, limit: number) {
    const [history, subscriptions, likes] = await Promise.all([
      this.prisma.watchHistory.findMany({
        where: { userId },
        include: { video: { select: { categoryId: true, tags: { select: { tagId: true } } } } },
        orderBy: { watchedAt: 'desc' },
        take: 50,
      }),
      this.prisma.subscription.findMany({
        where: { subscriberId: userId },
        select: { channelId: true },
      }),
      this.prisma.videoLike.findMany({
        where: { userId, isLike: true },
        include: { video: { select: { categoryId: true } } },
        take: 30,
      }),
    ]);

    const watchedIds = history.map(h => h.videoId);
    const categoryWeights = new Map<string, number>();
    const tagWeights = new Map<string, number>();

    history.forEach(h => {
      const catId = h.video.categoryId;
      if (catId) categoryWeights.set(catId, (categoryWeights.get(catId) || 0) + 1);
      h.video.tags.forEach(t => tagWeights.set(t.tagId, (tagWeights.get(t.tagId) || 0) + 1));
    });

    likes.forEach(l => {
      const catId = l.video.categoryId;
      if (catId) categoryWeights.set(catId, (categoryWeights.get(catId) || 0) + 2);
    });

    const topCategories = [...categoryWeights.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(e => e[0]);

    const topTags = [...tagWeights.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(e => e[0]);

    const channelIds = subscriptions.map(s => s.channelId);

    const recommendations = await this.prisma.video.findMany({
      where: {
        id: { notIn: watchedIds },
        status: 'READY',
        visibility: 'PUBLIC',
        isPublished: true,
        isDeleted: false,
        OR: [
          { categoryId: { in: topCategories } },
          { channelId: { in: channelIds } },
          { tags: { some: { tagId: { in: topTags } } } },
        ],
      },
      include: {
        channel: {
          select: { id: true, name: true, handle: true, avatar: true, isVerified: true, subscriberCount: true },
        },
      },
      take: limit * 2,
    });

    const scored = recommendations.map(r => ({
      ...r,
      score: this.calculatePersonalizedScore(r, channelIds, topCategories, topTags),
    }));

    scored.sort((a, b) => b.score - a.score);
    return { items: scored.slice(0, limit) };
  }

  private async getPopularVideos(limit: number) {
    const videos = await this.prisma.video.findMany({
      where: {
        status: 'READY',
        visibility: 'PUBLIC',
        isPublished: true,
        isDeleted: false,
      },
      include: {
        channel: {
          select: { id: true, name: true, handle: true, avatar: true, isVerified: true, subscriberCount: true },
        },
      },
      orderBy: { viewCount: 'desc' },
      take: limit,
    });

    return { items: videos };
  }

  private calculateScore(video: any, sourceChannelId: string, tagIds: string[]): number {
    let score = 0;
    if (video.channelId === sourceChannelId) score += 10;
    const matchingTags = video.tags?.filter((t: any) => tagIds.includes(t.tagId)).length || 0;
    score += matchingTags * 3;
    score += Math.log10(video.viewCount + 1) * 2;
    score += video.likeCount * 0.5;
    return score;
  }

  private calculatePersonalizedScore(video: any, channelIds: string[], topCategories: string[], topTags: string[]): number {
    let score = 0;
    if (channelIds.includes(video.channelId)) score += 15;
    if (topCategories.includes(video.categoryId)) score += 5;
    const matchingTags = video.tags?.filter((t: any) => topTags.includes(t.tagId)).length || 0;
    score += matchingTags * 2;
    score += Math.log10(video.viewCount + 1) * 2;
    score += video.likeCount * 0.3;
    const age = (Date.now() - new Date(video.publishedAt || video.createdAt).getTime()) / (1000 * 60 * 60 * 24);
    score += Math.max(0, 30 - age) * 0.5;
    return score;
  }
}
