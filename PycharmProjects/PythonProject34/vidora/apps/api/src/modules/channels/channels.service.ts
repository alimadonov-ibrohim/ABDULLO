import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class ChannelsService {
  constructor(private prisma: PrismaService) {}

  async getChannel(channelId: string) {
    const channel = await this.prisma.channel.findUnique({
      where: { id: channelId },
      include: {
        user: {
          select: { id: true, username: true, avatar: true },
        },
        _count: {
          select: {
            videos: { where: { status: 'READY', visibility: 'PUBLIC', isPublished: true } },
            subscriptions: true,
          },
        },
      },
    });
    if (!channel) throw new NotFoundException('Channel not found');
    return channel;
  }

  async getChannelByHandle(handle: string) {
    const channel = await this.prisma.channel.findUnique({
      where: { handle },
      include: {
        user: {
          select: { id: true, username: true, avatar: true },
        },
        _count: {
          select: {
            videos: { where: { status: 'READY', visibility: 'PUBLIC', isPublished: true } },
            subscriptions: true,
          },
        },
      },
    });
    if (!channel) throw new NotFoundException('Channel not found');
    return channel;
  }

  async getChannelVideos(channelId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [videos, total] = await Promise.all([
      this.prisma.video.findMany({
        where: {
          channelId,
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
        },
        include: {
          category: { select: { id: true, name: true, slug: true } },
        },
        orderBy: { publishedAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.video.count({
        where: {
          channelId,
          status: 'READY',
          visibility: 'PUBLIC',
          isPublished: true,
          isDeleted: false,
        },
      }),
    ]);

    return {
      items: videos,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async subscribe(subscriberId: string, channelId: string) {
    if (subscriberId === channelId) {
      throw new Error('Cannot subscribe to your own channel');
    }

    const existing = await this.prisma.subscription.findUnique({
      where: {
        subscriberId_channelId: { subscriberId, channelId },
      },
    });

    if (existing) {
      await this.prisma.subscription.delete({
        where: { id: existing.id },
      });
      await this.prisma.channel.update({
        where: { id: channelId },
        data: { subscriberCount: { decrement: 1 } },
      });
      return { subscribed: false };
    }

    await this.prisma.subscription.create({
      data: { subscriberId, channelId },
    });

    await this.prisma.channel.update({
      where: { id: channelId },
      data: { subscriberCount: { increment: 1 } },
    });

    await this.prisma.notification.create({
      data: {
        type: 'SUBSCRIPTION',
        message: 'subscribed to your channel',
        recipientId: (await this.prisma.channel.findUnique({ where: { id: channelId } }))!.userId,
        senderId: subscriberId,
        link: `/channel/${channelId}`,
      },
    });

    return { subscribed: true };
  }

  async getSubscribers(channelId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [subscribers, total] = await Promise.all([
      this.prisma.subscription.findMany({
        where: { channelId },
        include: {
          subscriber: {
            select: {
              id: true,
              username: true,
              avatar: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.subscription.count({ where: { channelId } }),
    ]);

    return {
      items: subscribers.map(s => s.subscriber),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getSubscriptions(userId: string, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    const [subscriptions, total] = await Promise.all([
      this.prisma.subscription.findMany({
        where: { subscriberId: userId },
        include: {
          channel: {
            select: {
              id: true,
              name: true,
              handle: true,
              avatar: true,
              isVerified: true,
              subscriberCount: true,
              videoCount: true,
            },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.subscription.count({ where: { subscriberId: userId } }),
    ]);

    return {
      items: subscriptions.map(s => s.channel),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async isSubscribed(userId: string, channelId: string): Promise<boolean> {
    const sub = await this.prisma.subscription.findUnique({
      where: {
        subscriberId_channelId: { subscriberId: userId, channelId },
      },
    });
    return !!sub;
  }
}
