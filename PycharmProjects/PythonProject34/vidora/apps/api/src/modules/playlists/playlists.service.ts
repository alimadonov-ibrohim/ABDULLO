import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class PlaylistsService {
  constructor(private prisma: PrismaService) {}

  async getUserPlaylists(userId: string) {
    return this.prisma.playlist.findMany({
      where: { userId },
      include: {
        items: {
          take: 3,
          include: {
            video: {
              select: { id: true, thumbnailUrl: true, title: true, duration: true },
            },
          },
          orderBy: { position: 'asc' },
        },
      },
      orderBy: { updatedAt: 'desc' },
    });
  }

  async getPlaylist(playlistId: string, userId?: string) {
    const playlist = await this.prisma.playlist.findUnique({
      where: { id: playlistId },
      include: {
        user: { select: { id: true, username: true } },
        items: {
          include: {
            video: {
              include: {
                channel: {
                  select: { id: true, name: true, avatar: true, isVerified: true },
                },
              },
            },
          },
          orderBy: { position: 'asc' },
        },
      },
    });

    if (!playlist) throw new NotFoundException('Playlist not found');
    if (!playlist.isPublic && playlist.userId !== userId) {
      throw new ForbiddenException('This playlist is private');
    }

    return playlist;
  }

  async createPlaylist(userId: string, dto: { name: string; description?: string; isPublic?: boolean }) {
    const channel = await this.prisma.channel.findFirst({ where: { userId } });

    return this.prisma.playlist.create({
      data: {
        name: dto.name,
        description: dto.description,
        isPublic: dto.isPublic ?? true,
        userId,
        channelId: channel?.id,
      },
    });
  }

  async updatePlaylist(playlistId: string, userId: string, dto: { name?: string; description?: string; isPublic?: boolean }) {
    const playlist = await this.prisma.playlist.findUnique({ where: { id: playlistId } });
    if (!playlist) throw new NotFoundException('Playlist not found');
    if (playlist.userId !== userId) throw new ForbiddenException('Not your playlist');

    return this.prisma.playlist.update({
      where: { id: playlistId },
      data: dto,
    });
  }

  async deletePlaylist(playlistId: string, userId: string) {
    const playlist = await this.prisma.playlist.findUnique({ where: { id: playlistId } });
    if (!playlist) throw new NotFoundException('Playlist not found');
    if (playlist.userId !== userId) throw new ForbiddenException('Not your playlist');

    await this.prisma.playlist.delete({ where: { id: playlistId } });
    return { success: true };
  }

  async addVideoToPlaylist(playlistId: string, userId: string, videoId: string) {
    const playlist = await this.prisma.playlist.findUnique({ where: { id: playlistId } });
    if (!playlist) throw new NotFoundException('Playlist not found');
    if (playlist.userId !== userId) throw new ForbiddenException('Not your playlist');

    const existing = await this.prisma.playlistItem.findUnique({
      where: { playlistId_videoId: { playlistId, videoId } },
    });
    if (existing) throw new ForbiddenException('Video already in playlist');

    const maxPosition = await this.prisma.playlistItem.aggregate({
      where: { playlistId },
      _max: { position: true },
    });

    const position = (maxPosition._max.position ?? -1) + 1;

    await this.prisma.playlistItem.create({
      data: { playlistId, videoId, position },
    });

    await this.prisma.playlist.update({
      where: { id: playlistId },
      data: { videoCount: { increment: 1 } },
    });

    return { success: true };
  }

  async removeVideoFromPlaylist(playlistId: string, userId: string, videoId: string) {
    const playlist = await this.prisma.playlist.findUnique({ where: { id: playlistId } });
    if (!playlist) throw new NotFoundException('Playlist not found');
    if (playlist.userId !== userId) throw new ForbiddenException('Not your playlist');

    await this.prisma.playlistItem.deleteMany({
      where: { playlistId, videoId },
    });

    await this.prisma.playlist.update({
      where: { id: playlistId },
      data: { videoCount: { decrement: 1 } },
    });

    return { success: true };
  }

  async reorderPlaylist(playlistId: string, userId: string, videoIds: string[]) {
    const playlist = await this.prisma.playlist.findUnique({ where: { id: playlistId } });
    if (!playlist) throw new NotFoundException('Playlist not found');
    if (playlist.userId !== userId) throw new ForbiddenException('Not your playlist');

    for (let i = 0; i < videoIds.length; i++) {
      await this.prisma.playlistItem.updateMany({
        where: { playlistId, videoId: videoIds[i] },
        data: { position: i },
      });
    }

    return { success: true };
  }
}
