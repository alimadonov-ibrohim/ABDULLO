import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../../common/storage/storage.service';

@Injectable()
export class UsersService {
  constructor(
    private prisma: PrismaService,
    private storage: StorageService,
  ) {}

  async getProfile(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: {
        channel: {
          select: {
            id: true,
            name: true,
            handle: true,
            avatar: true,
            subscriberCount: true,
            videoCount: true,
            isVerified: true,
          },
        },
        _count: {
          select: { subscriptions: true },
        },
      },
    });
    if (!user) throw new NotFoundException('User not found');
    return this.sanitize(user);
  }

  async updateProfile(userId: string, dto: { username?: string; description?: string }) {
    return this.prisma.user.update({
      where: { id: userId },
      data: dto,
      select: {
        id: true,
        email: true,
        username: true,
        avatar: true,
        description: true,
        role: true,
        createdAt: true,
      },
    });
  }

  async uploadAvatar(userId: string, file: Express.Multer.File) {
    const key = `avatars/${userId}/${Date.now()}-${file.originalname}`;
    const url = await this.storage.uploadFile(key, file.buffer, file.mimetype);

    await this.prisma.user.update({
      where: { id: userId },
      data: { avatar: url },
    });

    return { url };
  }

  async uploadBanner(userId: string, file: Express.Multer.File) {
    const key = `banners/${userId}/${Date.now()}-${file.originalname}`;
    const url = await this.storage.uploadFile(key, file.buffer, file.mimetype);

    await this.prisma.user.update({
      where: { id: userId },
      data: { banner: url },
    });

    return { url };
  }

  async getUserPublicProfile(username: string) {
    const user = await this.prisma.user.findFirst({
      where: {
        OR: [
          { username },
          { channel: { handle: username } },
        ],
      },
      include: {
        channel: {
          select: {
            id: true,
            name: true,
            handle: true,
            avatar: true,
            banner: true,
            description: true,
            subscriberCount: true,
            videoCount: true,
            totalViews: true,
            isVerified: true,
            createdAt: true,
          },
        },
        _count: {
          select: { subscriptions: true },
        },
      },
    });
    if (!user) throw new NotFoundException('User not found');
    return this.sanitize(user);
  }

  private sanitize(user: any) {
    const { passwordHash, googleId, githubId, refreshTokens, sessions, ...rest } = user;
    return rest;
  }
}
