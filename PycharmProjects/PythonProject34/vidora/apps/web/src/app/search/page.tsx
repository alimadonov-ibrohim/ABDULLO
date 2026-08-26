'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { useSearch } from '@/hooks';
import { cn } from '@/lib/utils';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  const [type, setType] = useState('videos');
  const [sortBy, setSortBy] = useState('relevance');

  const { data: results, isLoading } = useSearch(query, { type, sortBy });

  return (
    <Layout>
      <div className="max-w-5xl mx-auto p-4 md:p-6">
        {query && (
          <div className="mb-6">
            <h1 className="text-lg text-white mb-4">
              Results for &quot;{query}&quot;
            </h1>

            {/* Filters */}
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                {['videos', 'channels', 'playlists'].map((t) => (
                  <button
                    key={t}
                    onClick={() => setType(t)}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                      type === t
                        ? 'bg-white text-black'
                        : 'bg-surface-dark-elevated text-gray-300 hover:bg-gray-600'
                    )}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-surface-dark-elevated text-gray-300 text-sm px-3 py-1.5 rounded-lg border-none focus:outline-none"
              >
                <option value="relevance">Relevance</option>
                <option value="date">Upload date</option>
                <option value="views">View count</option>
                <option value="rating">Rating</option>
              </select>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <VideoCardSkeleton key={i} />
            ))}
          </div>
        ) : results?.items?.length > 0 ? (
          <div className="space-y-4">
            {results.items.map((video: any) => (
              <VideoCard key={video.id} video={video} layout="list" />
            ))}
          </div>
        ) : query ? (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400 text-lg">No results found for &quot;{query}&quot;</p>
            <p className="text-gray-500 text-sm mt-2">Try different keywords</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400 text-lg">Search for videos</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
