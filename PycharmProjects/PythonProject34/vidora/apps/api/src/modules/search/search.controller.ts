import { Controller, Get, Post, Query, Param } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { SearchService } from './search.service';
import { CurrentUser, Public } from '../../common/decorators/auth.decorators';

@ApiTags('search')
@Controller('search')
export class SearchController {
  constructor(private searchService: SearchService) {}

  @Get()
  @Public()
  @ApiOperation({ summary: 'Search videos, channels, playlists' })
  async search(
    @Query('q') q: string,
    @Query('type') type?: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
    @Query('sortBy') sortBy?: string,
    @Query('dateFilter') dateFilter?: string,
    @Query('durationFilter') durationFilter?: string,
  ) {
    return this.searchService.search(q, { type, page, limit, sortBy, dateFilter, durationFilter });
  }

  @Get('suggestions')
  @Public()
  @ApiOperation({ summary: 'Get search suggestions' })
  async getSuggestions(@Query('q') q: string) {
    return this.searchService.getSearchSuggestions(q);
  }

  @Get('history')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get search history' })
  async getHistory(@CurrentUser() user: any) {
    return this.searchService.getSearchHistory(user.id);
  }

  @Post('history')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Save search query' })
  async saveHistory(@CurrentUser() user: any, @Query('q') q: string) {
    return this.searchService.saveSearchHistory(user.id, q);
  }
}
