'use client';

import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { useTrendingVideos } from '@/hooks';

export default function TrendingPage() {
  const { data: videos, isLoading } = useTrendingVideos({ limit: 30 });

  return (
    <Layout>
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-4">Trending</h1>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <VideoCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {videos?.items?.map((video: any) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
