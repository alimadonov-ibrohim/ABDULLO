export interface Playlist {
  id: string;
  name: string;
  description?: string | null;
  isPublic: boolean;
  thumbnailUrl?: string | null;
  videoCount: number;
  createdAt: Date;
  updatedAt: Date;
  userId: string;
  channelId?: string | null;
}

export interface PlaylistWithVideos extends Playlist {
  items: {
    id: string;
    position: number;
    addedAt: Date;
    video: import('./video').VideoListItem;
  }[];
}

export interface CreatePlaylistDto {
  name: string;
  description?: string;
  isPublic?: boolean;
}

export interface UpdatePlaylistDto extends Partial<CreatePlaylistDto> {}
