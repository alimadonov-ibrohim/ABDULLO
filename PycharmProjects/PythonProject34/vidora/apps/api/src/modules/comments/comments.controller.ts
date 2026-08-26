import { Controller, Get, Post, Delete, Body, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { CommentsService } from './comments.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('comments')
@Controller('comments')
export class CommentsController {
  constructor(private commentsService: CommentsService) {}

  @Get('video/:videoId')
  @Public()
  @ApiOperation({ summary: 'Get video comments' })
  async getComments(
    @Param('videoId') videoId: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('sortBy') sortBy?: string,
  ) {
    return this.commentsService.getComments(videoId, page, limit, sortBy);
  }

  @Get(':id/replies')
  @Public()
  @ApiOperation({ summary: 'Get comment replies' })
  async getReplies(
    @Param('id') id: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
  ) {
    return this.commentsService.getReplies(id, page, limit);
  }

  @Post()
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create comment' })
  async createComment(
    @CurrentUser() user: any,
    @Body() body: { text: string; videoId: string; parentId?: string },
  ) {
    return this.commentsService.createComment(user.id, body);
  }

  @Delete(':id')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete comment' })
  async deleteComment(@Param('id') id: string, @CurrentUser() user: any) {
    return this.commentsService.deleteComment(id, user.id);
  }

  @Post(':id/like')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Like/unlike comment' })
  async likeComment(@Param('id') id: string, @CurrentUser() user: any) {
    return this.commentsService.likeComment(user.id, id);
  }
}
