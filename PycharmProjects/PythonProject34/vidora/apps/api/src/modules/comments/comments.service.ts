import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class CommentsService {
  constructor(private prisma: PrismaService) {}

  async getComments(videoId: string, page = 1, limit = 20, sortBy = 'newest') {
    const skip = (page - 1) * limit;

    const orderBy: any = sortBy === 'top'
      ? { likeCount: 'desc' }
      : { createdAt: 'desc' };

    const [comments, total] = await Promise.all([
      this.prisma.comment.findMany({
        where: {
          videoId,
          parentId: null,
          isDeleted: false,
        },
        include: {
          user: {
            select: {
              id: true,
              username: true,
              avatar: true,
              channel: {
                select: { id: true, name: true, avatar: true, isVerified: true },
              },
            },
          },
          _count: {
            select: { replies: { where: { isDeleted: false } } },
          },
        },
        orderBy,
        skip,
        take: limit,
      }),
      this.prisma.comment.count({
        where: { videoId, parentId: null, isDeleted: false },
      }),
    ]);

    return {
      items: comments.map(c => ({ ...c, replyCount: c._count.replies })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getReplies(commentId: string, page = 1, limit = 10) {
    const skip = (page - 1) * limit;
    const [replies, total] = await Promise.all([
      this.prisma.comment.findMany({
        where: { parentId: commentId, isDeleted: false },
        include: {
          user: {
            select: { id: true, username: true, avatar: true },
          },
        },
        orderBy: { createdAt: 'asc' },
        skip,
        take: limit,
      }),
      this.prisma.comment.count({ where: { parentId: commentId, isDeleted: false } }),
    ]);

    return { items: replies, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async createComment(userId: string, dto: { text: string; videoId: string; parentId?: string }) {
    const video = await this.prisma.video.findUnique({ where: { id: dto.videoId } });
    if (!video) throw new NotFoundException('Video not found');

    if (dto.parentId) {
      const parent = await this.prisma.comment.findUnique({ where: { id: dto.parentId } });
      if (!parent) throw new NotFoundException('Parent comment not found');
    }

    const comment = await this.prisma.comment.create({
      data: {
        text: dto.text,
        userId,
        videoId: dto.videoId,
        parentId: dto.parentId,
        channelId: video.channelId,
      },
      include: {
        user: {
          select: { id: true, username: true, avatar: true },
        },
      },
    });

    await this.prisma.video.update({
      where: { id: dto.videoId },
      data: { commentCount: { increment: 1 } },
    });

    if (dto.parentId) {
      await this.prisma.comment.update({
        where: { id: dto.parentId },
        data: { replyCount: { increment: 1 } },
      });
    }

    return comment;
  }

  async deleteComment(commentId: string, userId: string) {
    const comment = await this.prisma.comment.findUnique({ where: { id: commentId } });
    if (!comment) throw new NotFoundException('Comment not found');
    if (comment.userId !== userId) throw new ForbiddenException('Not your comment');

    await this.prisma.comment.update({
      where: { id: commentId },
      data: { isDeleted: true, text: '[deleted]' },
    });

    return { success: true };
  }

  async likeComment(userId: string, commentId: string) {
    const existing = await this.prisma.commentLike.findUnique({
      where: { userId_commentId: { userId, commentId } },
    });

    if (existing) {
      await this.prisma.commentLike.delete({ where: { id: existing.id } });
      await this.prisma.comment.update({
        where: { id: commentId },
        data: { likeCount: { decrement: 1 } },
      });
      return { liked: false };
    }

    await this.prisma.commentLike.create({
      data: { userId, commentId },
    });

    await this.prisma.comment.update({
      where: { id: commentId },
      data: { likeCount: { increment: 1 } },
    });

    return { liked: true };
  }
}
