'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { VideoCard, VideoCardSkeleton } from '@/components/video/VideoCard';
import { useChannel, useChannelVideos, useSubscribe } from '@/hooks';
import { useAuthStore } from '@/stores';
import { cn, formatViews } from '@/lib/utils';
import { useState } from 'react';

export default function ChannelPage() {
  const params = useParams();
  const handle = params.channelId as string;
  const { isAuthenticated } = useAuthStore();
  const [tab, setTab] = useState<'videos' | 'shorts' | 'playlists'>('videos');

  const { data: channel, isLoading: channelLoading } = useChannel(handle);
  const { data: videosData, isLoading: videosLoading } = useChannelVideos(channel?.id || '', { limit: 50 });
  const subscribeMutation = useSubscribe();

  if (channelLoading) {
    return (
      <Layout>
        <div className="animate-pulse">
          <div className="h-48 bg-gray-800" />
          <div className="max-w-5xl mx-auto px-4 -mt-12">
            <div className="flex items-end gap-4">
              <div className="w-24 h-24 rounded-full bg-gray-700 border-4 border-surface-dark" />
              <div className="pb-4">
                <div className="h-6 bg-gray-800 rounded w-48 mb-2" />
                <div className="h-4 bg-gray-800 rounded w-32" />
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!channel) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <p className="text-gray-400">Channel not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Banner */}
      <div className="h-48 bg-gradient-to-r from-vidora-900 to-vidora-700">
        {channel.banner && (
          <img src={channel.banner} alt="" className="w-full h-full object-cover" />
        )}
      </div>

      {/* Channel Info */}
      <div className="max-w-5xl mx-auto px-4 -mt-12">
        <div className="flex items-end gap-4 mb-6">
          <div className="w-24 h-24 rounded-full bg-gray-700 border-4 border-surface-dark overflow-hidden flex-shrink-0">
            {channel.avatar ? (
              <img src={channel.avatar} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="w-full h-full flex items-center justify-center text-2xl text-white font-bold">
                {channel.name.charAt(0)}
              </span>
            )}
          </div>
          <div className="flex-1 pb-1">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              {channel.name}
              {channel.isVerified && <span className="text-gray-400 text-sm">✓</span>}
            </h1>
            <p className="text-sm text-gray-400">
              @{channel.handle} &middot; {channel._count?.subscriptions?.toLocaleString()} subscribers &middot; {channel._count?.videos} videos
            </p>
          </div>
          {isAuthenticated && (
            <button
              onClick={() => subscribeMutation.mutate(channel.id)}
              className="px-6 py-2.5 bg-white text-black rounded-full font-medium hover:bg-gray-200 transition-colors mb-1"
            >
              Subscribe
            </button>
          )}
        </div>

        {channel.description && (
          <p className="text-sm text-gray-400 mb-6 max-w-2xl">{channel.description}</p>
        )}

        {/* Tabs */}
        <div className="flex gap-6 border-b border-gray-700 mb-6">
          {(['videos', 'shorts', 'playlists'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                'pb-3 text-sm font-medium capitalize transition-colors border-b-2',
                tab === t
                  ? 'text-white border-white'
                  : 'text-gray-400 border-transparent hover:text-gray-300'
              )}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Videos */}
        {videosLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {Array.from({ length: 8 }).map((_, i) => <VideoCardSkeleton key={i} />)}
          </div>
        ) : videosData?.items?.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {videosData.items.map((v: any) => <VideoCard key={v.id} video={v} />)}
          </div>
        ) : (
          <div className="text-center py-20">
            <p className="text-gray-400">No videos yet</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
