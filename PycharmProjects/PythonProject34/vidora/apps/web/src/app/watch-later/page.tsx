'use client';

import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { useWatchLater } from '@/hooks';

export default function WatchLaterPage() {
  const { data, isLoading } = useWatchLater({ limit: 50 });

  return (
    <Layout>
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-4">Watch Later</h1>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {Array.from({ length: 8 }).map((_, i) => <VideoCardSkeleton key={i} />)}
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {data.items.map((v: any) => <VideoCard key={v.id} video={v} />)}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400">No videos saved for later</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
