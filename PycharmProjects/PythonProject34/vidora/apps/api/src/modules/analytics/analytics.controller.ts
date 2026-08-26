import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { AnalyticsService } from './analytics.service';
import { CurrentUser } from '../../common/decorators/auth.decorators';

@ApiTags('analytics')
@Controller('analytics')
@ApiBearerAuth()
export class AnalyticsController {
  constructor(private analyticsService: AnalyticsService) {}

  @Get('channel/:channelId')
  @ApiOperation({ summary: 'Get channel analytics' })
  async getChannelAnalytics(
    @Param('channelId') channelId: string,
    @Query('days') days?: number,
  ) {
    return this.analyticsService.getChannelAnalytics(channelId, days);
  }

  @Get('video/:videoId')
  @ApiOperation({ summary: 'Get video analytics' })
  async getVideoAnalytics(
    @Param('videoId') videoId: string,
    @Query('days') days?: number,
  ) {
    return this.analyticsService.getVideoAnalytics(videoId, days);
  }
}
