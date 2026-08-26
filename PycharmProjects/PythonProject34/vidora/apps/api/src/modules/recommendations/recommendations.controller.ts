import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { RecommendationsService } from './recommendations.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('recommendations')
@Controller('recommendations')
export class RecommendationsController {
  constructor(private recommendationsService: RecommendationsService) {}

  @Get('home')
  @Public()
  @ApiOperation({ summary: 'Get home page recommendations' })
  async getHomeRecommendations(
    @CurrentUser() user: any,
    @Query('limit') limit?: number,
  ) {
    return this.recommendationsService.getHomeRecommendations(user?.id, limit);
  }

  @Get('watch/:videoId')
  @Public()
  @ApiOperation({ summary: 'Get video recommendations' })
  async getVideoRecommendations(
    @Param('videoId') videoId: string,
    @CurrentUser() user: any,
    @Query('limit') limit?: number,
  ) {
    return this.recommendationsService.getVideoRecommendations(videoId, user?.id, limit);
  }
}
