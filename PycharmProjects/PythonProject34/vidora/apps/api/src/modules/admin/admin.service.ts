import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AdminService {
  constructor(private prisma: PrismaService) {}

  async getDashboardStats() {
    const [
      totalUsers,
      activeUsers,
      totalVideos,
      totalViews,
      totalComments,
      pendingReports,
      processingJobs,
    ] = await Promise.all([
      this.prisma.user.count(),
      this.prisma.user.count({
        where: { updatedAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } },
      }),
      this.prisma.video.count({ where: { isDeleted: false } }),
      this.prisma.videoView.count(),
      this.prisma.comment.count({ where: { isDeleted: false } }),
      this.prisma.videoReport.count({ where: { status: 'PENDING' } })
        .then(async (v) => {
          const c = await this.prisma.commentReport.count({ where: { status: 'PENDING' } });
          const ch = await this.prisma.channelReport.count({ where: { status: 'PENDING' } });
          return v + c + ch;
        }),
      this.prisma.videoProcessingJob.count({ where: { status: 'pending' } }),
    ]);

    return {
      totalUsers,
      activeUsers,
      totalVideos,
      totalViews,
      totalComments,
      pendingReports,
      processingJobs,
    };
  }

  async getUsers(page = 1, limit = 20, search?: string) {
    const skip = (page - 1) * limit;
    const where = search
      ? {
          OR: [
            { username: { contains: search, mode: 'insensitive' as const } },
            { email: { contains: search, mode: 'insensitive' as const } },
          ],
        }
      : {};

    const [users, total] = await Promise.all([
      this.prisma.user.findMany({
        where,
        select: {
          id: true, email: true, username: true, role: true, isVerified: true,
          createdAt: true, updatedAt: true,
          channel: { select: { subscriberCount: true, videoCount: true } },
        },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.user.count({ where }),
    ]);

    return { items: users, total, page, limit, totalPages: Math.ceil(total / limit) };
  }

  async updateUserRole(userId: string, role: string) {
    return this.prisma.user.update({
      where: { id: userId },
      data: { role: role as any },
      select: { id: true, username: true, role: true },
    });
  }

  async deleteUser(userId: string) {
    await this.prisma.user.delete({ where: { id: userId } });
    return { success: true };
  }

  async getReports(type = 'all', status = 'PENDING', page = 1, limit = 20) {
    const skip = (page - 1) * limit;

    if (type === 'videos' || type === 'all') {
      const [reports, total] = await Promise.all([
        this.prisma.videoReport.findMany({
          where: { status: status as any },
          include: {
            user: { select: { id: true, username: true } },
            video: { select: { id: true, title: true } },
          },
          orderBy: { createdAt: 'desc' },
          skip,
          take: limit,
        }),
        this.prisma.videoReport.count({ where: { status: status as any } }),
      ]);
      return { items: reports, total, page, limit, totalPages: Math.ceil(total / limit) };
    }

    if (type === 'comments') {
      const [reports, total] = await Promise.all([
        this.prisma.commentReport.findMany({
          where: { status: status as any },
          include: {
            user: { select: { id: true, username: true } },
            comment: { select: { id: true, text: true } },
          },
          orderBy: { createdAt: 'desc' },
          skip,
          take: limit,
        }),
        this.prisma.commentReport.count({ where: { status: status as any } }),
      ]);
      return { items: reports, total, page, limit, totalPages: Math.ceil(total / limit) };
    }

    return { items: [], total: 0, page, limit, totalPages: 0 };
  }

  async resolveReport(reportId: string, status: string) {
    const report = await this.prisma.videoReport.findUnique({ where: { id: reportId } });
    if (report) {
      return this.prisma.videoReport.update({ where: { id: reportId }, data: { status: status as any } });
    }
    const cReport = await this.prisma.commentReport.findUnique({ where: { id: reportId } });
    if (cReport) {
      return this.prisma.commentReport.update({ where: { id: reportId }, data: { status: status as any } });
    }
    return this.prisma.channelReport.update({ where: { id: reportId }, data: { status: status as any } });
  }

  async getVideos(page = 1, limit = 20, search?: string) {
    const skip = (page - 1) * limit;
    const where: any = search
      ? { OR: [{ title: { contains: search, mode: 'insensitive' } }] }
      : {};

    const [videos, total] = await Promise.all([
      this.prisma.video.findMany({
        where,
        include: { channel: { select: { id: true, name: true } } },
        orderBy: { createdAt: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.video.count({ where }),
    ]);

    return { items: videos, total, page, limit, totalPages: Math.ceil(total / limit) };
  }
}
