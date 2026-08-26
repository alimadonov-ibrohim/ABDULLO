export interface Channel {
  id: string;
  name: string;
  handle: string;
  description?: string | null;
  avatar?: string | null;
  banner?: string | null;
  subscriberCount: number;
  videoCount: number;
  totalViews: bigint;
  isVerified: boolean;
  createdAt: Date;
  updatedAt: Date;
  userId: string;
}

export interface ChannelWithVideos extends Channel {
  videos: import('./video').VideoListItem[];
  _count: {
    videos: number;
    subscriptions: number;
  };
}
