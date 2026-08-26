'use client';

import { Layout } from '@/components/layout/Layout';
import { useVideos } from '@/hooks';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { Film } from 'lucide-react';
import Link from 'next/link';

export default function SubscriptionsPage() {
  const { data: videos, isLoading } = useVideos({ limit: 30, sortBy: 'publishedAt' });

  return (
    <Layout>
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-4">Subscriptions</h1>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {Array.from({ length: 8 }).map((_, i) => <VideoCardSkeleton key={i} />)}
          </div>
        ) : videos?.items?.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {videos.items.map((v: any) => <VideoCard key={v.id} video={v} />)}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20">
            <Film className="w-12 h-12 text-gray-600 mb-4" />
            <p className="text-gray-400 mb-2">No subscriptions yet</p>
            <p className="text-sm text-gray-500">Subscribe to channels to see their latest videos here</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
