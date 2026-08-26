export interface Video {
  id: string;
  title: string;
  description?: string | null;
  thumbnailUrl?: string | null;
  videoUrl?: string | null;
  hlsUrl?: string | null;
  duration?: number | null;
  status: string;
  visibility: string;
  viewCount: number;
  likeCount: number;
  dislikeCount: number;
  commentCount: number;
  isPublished: boolean;
  publishedAt?: Date | null;
  language?: string | null;
  createdAt: Date;
  updatedAt: Date;
  channelId: string;
  channel: {
    id: string;
    name: string;
    handle: string;
    avatar?: string | null;
    isVerified: boolean;
    subscriberCount: number;
  };
  category?: {
    id: string;
    name: string;
    slug: string;
  } | null;
  tags?: { tag: { id: string; name: string; slug: string } }[];
}

export interface VideoListItem {
  id: string;
  title: string;
  thumbnailUrl?: string | null;
  duration?: number | null;
  viewCount: number;
  publishedAt?: Date | null;
  createdAt: Date;
  channel: {
    id: string;
    name: string;
    handle: string;
    avatar?: string | null;
    isVerified: boolean;
  };
}

export interface CreateVideoDto {
  title: string;
  description?: string;
  categoryId?: string;
  tags?: string[];
  visibility?: 'PUBLIC' | 'UNLISTED' | 'PRIVATE';
  language?: string;
  playlistId?: string;
}

export interface UpdateVideoDto extends Partial<CreateVideoDto> {}

export interface VideoQuery {
  page?: number;
  limit?: number;
  category?: string;
  sortBy?: 'viewCount' | 'publishedAt' | 'createdAt' | 'likeCount';
  sortOrder?: 'asc' | 'desc';
  channelId?: string;
}
