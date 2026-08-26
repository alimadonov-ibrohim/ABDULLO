'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { CategoryChips } from '@/components/video/CategoryChips';
import { useHomeRecommendations } from '@/hooks';

export default function HomePage() {
  const [category, setCategory] = useState('All');
  const { data: videos, isLoading, error } = useHomeRecommendations();

  return (
    <Layout>
      <div className="sticky top-[56px] z-30 bg-surface-dark">
        <CategoryChips selected={category} onSelect={setCategory} />
      </div>

      <div className="p-4 md:p-6">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <VideoCardSkeleton key={i} />
            ))}
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400 text-lg">Something went wrong</p>
            <p className="text-gray-500 text-sm mt-2">Please try again later</p>
          </div>
        ) : videos && videos.items && videos.items.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {videos.items.map((video: any) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400 text-lg">No videos found</p>
            <p className="text-gray-500 text-sm mt-2">Upload some videos to get started</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
