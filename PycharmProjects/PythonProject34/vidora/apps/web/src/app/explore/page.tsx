'use client';

import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { useVideos } from '@/hooks';
import { CategoryChips } from '@/components/video/CategoryChips';
import { useState } from 'react';

export default function ExplorePage() {
  const [category, setCategory] = useState('All');
  const { data: videos, isLoading } = useVideos({
    category: category === 'All' ? undefined : category,
    sortBy: 'viewCount',
    limit: 30,
  });

  return (
    <Layout>
      <CategoryChips selected={category} onSelect={setCategory} />
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-4">Explore</h1>
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
