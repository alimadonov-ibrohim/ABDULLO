import { Controller, Get, Post, Patch, Delete, Body, Param } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { PlaylistsService } from './playlists.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('playlists')
@Controller('playlists')
export class PlaylistsController {
  constructor(private playlistsService: PlaylistsService) {}

  @Get('me')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get my playlists' })
  async getMyPlaylists(@CurrentUser() user: any) {
    return this.playlistsService.getUserPlaylists(user.id);
  }

  @Get(':id')
  @Public()
  @ApiOperation({ summary: 'Get playlist' })
  async getPlaylist(@Param('id') id: string, @CurrentUser() user: any) {
    return this.playlistsService.getPlaylist(id, user?.id);
  }

  @Post()
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create playlist' })
  async createPlaylist(
    @CurrentUser() user: any,
    @Body() body: { name: string; description?: string; isPublic?: boolean },
  ) {
    return this.playlistsService.createPlaylist(user.id, body);
  }

  @Patch(':id')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update playlist' })
  async updatePlaylist(
    @Param('id') id: string,
    @CurrentUser() user: any,
    @Body() body: { name?: string; description?: string; isPublic?: boolean },
  ) {
    return this.playlistsService.updatePlaylist(id, user.id, body);
  }

  @Delete(':id')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete playlist' })
  async deletePlaylist(@Param('id') id: string, @CurrentUser() user: any) {
    return this.playlistsService.deletePlaylist(id, user.id);
  }

  @Post(':id/videos')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Add video to playlist' })
  async addVideo(
    @Param('id') id: string,
    @CurrentUser() user: any,
    @Body('videoId') videoId: string,
  ) {
    return this.playlistsService.addVideoToPlaylist(id, user.id, videoId);
  }

  @Delete(':id/videos/:videoId')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Remove video from playlist' })
  async removeVideo(
    @Param('id') id: string,
    @Param('videoId') videoId: string,
    @CurrentUser() user: any,
  ) {
    return this.playlistsService.removeVideoFromPlaylist(id, user.id, videoId);
  }

  @Patch(':id/reorder')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Reorder playlist videos' })
  async reorder(
    @Param('id') id: string,
    @CurrentUser() user: any,
    @Body('videoIds') videoIds: string[],
  ) {
    return this.playlistsService.reorderPlaylist(id, user.id, videoIds);
  }
}
