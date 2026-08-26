import {
  Controller, Get, Post, Patch, Delete, Body, Param, Query, UseInterceptors, UploadedFile, UploadedFiles,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiConsumes } from '@nestjs/swagger';
import { FileInterceptor, FilesInterceptor } from '@nestjs/platform-express';
import { VideosService } from './videos.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('videos')
@Controller('videos')
export class VideosController {
  constructor(private videosService: VideosService) {}

  @Get()
  @Public()
  @ApiOperation({ summary: 'Get videos feed' })
  async getVideos(
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('category') category?: string,
    @Query('sortBy') sortBy?: string,
    @Query('sortOrder') sortOrder?: string,
    @Query('channelId') channelId?: string,
  ) {
    return this.videosService.getVideos({ page, limit, category, sortBy, sortOrder, channelId });
  }

  @Get('trending')
  @Public()
  @ApiOperation({ summary: 'Get trending videos' })
  async getTrending(@Query('page') page?: number, @Query('limit') limit?: number) {
    return this.videosService.getTrending(page, limit);
  }

  @Get('shorts')
  @Public()
  @ApiOperation({ summary: 'Get shorts' })
  async getShorts(@Query('page') page?: number, @Query('limit') limit?: number) {
    return this.videosService.getShorts(page, limit);
  }

  @Get('history')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get watch history' })
  async getHistory(@CurrentUser() user: any, @Query('page') page?: number, @Query('limit') limit?: number) {
    return this.videosService.getUserHistory(user.id, page, limit);
  }

  @Get('watch-later')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get watch later list' })
  async getWatchLater(@CurrentUser() user: any, @Query('page') page?: number, @Query('limit') limit?: number) {
    return this.videosService.getWatchLater(user.id, page, limit);
  }

  @Get('liked')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get liked videos' })
  async getLiked(@CurrentUser() user: any, @Query('page') page?: number, @Query('limit') limit?: number) {
    return this.videosService.getLikedVideos(user.id, page, limit);
  }

  @Get(':id')
  @Public()
  @ApiOperation({ summary: 'Get video by ID' })
  async getVideo(@Param('id') id: string) {
    return this.videosService.getVideoById(id);
  }

  @Post('upload-url')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get presigned upload URL' })
  async getUploadUrl(
    @CurrentUser() user: any,
    @Body() body: { filename: string; contentType: string },
  ) {
    return this.videosService.getUploadUrl(user.id, body);
  }

  @Post()
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create video metadata' })
  async createVideo(
    @CurrentUser() user: any,
    @Body() body: {
      title: string;
      description?: string;
      categoryId?: string;
      tags?: string[];
      visibility?: string;
      language?: string;
    },
  ) {
    return this.videosService.createVideo(user.id, body);
  }

  @Patch(':id')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update video' })
  async updateVideo(
    @Param('id') id: string,
    @CurrentUser() user: any,
    @Body() body: {
      title?: string;
      description?: string;
      categoryId?: string;
      visibility?: string;
      language?: string;
    },
  ) {
    return this.videosService.updateVideo(id, user.id, body);
  }

  @Delete(':id')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete video' })
  async deleteVideo(@Param('id') id: string, @CurrentUser() user: any) {
    return this.videosService.deleteVideo(id, user.id);
  }

  @Post(':id/like')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Like/Dislike video' })
  async likeVideo(
    @Param('id') id: string,
    @CurrentUser() user: any,
    @Body('isLike') isLike: boolean,
  ) {
    return this.videosService.likeVideo(user.id, id, isLike);
  }

  @Post(':id/view')
  @Public()
  @ApiOperation({ summary: 'Record video view' })
  async recordView(
    @Param('id') id: string,
    @CurrentUser() user: any,
  ) {
    return this.videosService.recordView(user?.id || null, id, '');
  }

  @Post(':id/publish')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Publish video' })
  async publishVideo(@Param('id') id: string, @CurrentUser() user: any) {
    return this.videosService.publishVideo(id, user.id);
  }

  @Post(':id/process')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Start video processing' })
  async processVideo(@Param('id') id: string) {
    return this.videosService.processVideo(id);
  }
}
