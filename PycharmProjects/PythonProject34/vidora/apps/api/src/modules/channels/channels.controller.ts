import { Controller, Get, Post, Delete, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { ChannelsService } from './channels.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('channels')
@Controller('channels')
export class ChannelsController {
  constructor(private channelsService: ChannelsService) {}

  @Get(':id')
  @Public()
  @ApiOperation({ summary: 'Get channel by ID' })
  async getChannel(@Param('id') id: string) {
    return this.channelsService.getChannel(id);
  }

  @Get('handle/:handle')
  @Public()
  @ApiOperation({ summary: 'Get channel by handle' })
  async getChannelByHandle(@Param('handle') handle: string) {
    return this.channelsService.getChannelByHandle(handle);
  }

  @Get(':id/videos')
  @Public()
  @ApiOperation({ summary: 'Get channel videos' })
  async getChannelVideos(
    @Param('id') id: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
  ) {
    return this.channelsService.getChannelVideos(id, page, limit);
  }

  @Post(':id/subscribe')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Subscribe/Unsubscribe to channel' })
  async toggleSubscription(@CurrentUser() user: any, @Param('id') id: string) {
    return this.channelsService.subscribe(user.id, id);
  }

  @Get(':id/subscribers')
  @Public()
  @ApiOperation({ summary: 'Get channel subscribers' })
  async getSubscribers(
    @Param('id') id: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
  ) {
    return this.channelsService.getSubscribers(id, page, limit);
  }

  @Get('subscriptions')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get user subscriptions' })
  async getSubscriptions(
    @CurrentUser() user: any,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
  ) {
    return this.channelsService.getSubscriptions(user.id, page, limit);
  }
}
