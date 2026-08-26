'use client';

import Link from 'next/link';
import { useState } from 'react';
import { MoreVertical, Clock, ListPlus } from 'lucide-react';
import { cn, formatDuration, formatViews, formatRelativeTime } from '@/lib/utils';

interface VideoCardProps {
  video: {
    id: string;
    title: string;
    thumbnailUrl?: string | null;
    duration?: number | null;
    viewCount: number;
    publishedAt?: string | null;
    createdAt: string;
    channel: {
      id: string;
      name: string;
      handle: string;
      avatar?: string | null;
      isVerified: boolean;
    };
  };
  layout?: 'grid' | 'list';
}

export function VideoCard({ video, layout = 'grid' }: VideoCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const thumbnailUrl = video.thumbnailUrl || `/api/placeholder/640/360`;

  if (layout === 'list') {
    return (
      <div className="flex gap-4 group">
        <Link href={`/watch/${video.id}`} className="flex-shrink-0 relative w-[400px] aspect-video rounded-xl overflow-hidden bg-gray-800">
          <img
            src={thumbnailUrl}
            alt={video.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          {video.duration && (
            <span className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/80 text-white text-xs font-medium rounded">
              {formatDuration(video.duration)}
            </span>
          )}
        </Link>
        <div className="flex-1 min-w-0">
          <Link href={`/watch/${video.id}`}>
            <h3 className="text-white font-medium line-clamp-2 mb-1 group-hover:text-vidora-400 transition-colors">
              {video.title}
            </h3>
          </Link>
          <p className="text-sm text-gray-400">
            {formatViews(video.viewCount)} views &middot; {formatRelativeTime(video.publishedAt || video.createdAt)}
          </p>
          <Link href={`/channel/${video.channel.handle}`} className="flex items-center gap-2 mt-2 group/channel">
            <div className="w-6 h-6 rounded-full bg-gray-600 overflow-hidden">
              {video.channel.avatar ? (
                <img src={video.channel.avatar} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="w-full h-full flex items-center justify-center text-xs text-white font-medium">
                  {video.channel.name.charAt(0)}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400 group-hover/channel:text-gray-300">{video.channel.name}</span>
            {video.channel.isVerified && (
              <span className="text-[10px] text-gray-400">✓</span>
            )}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="group relative">
      <Link href={`/watch/${video.id}`} className="relative aspect-video rounded-xl overflow-hidden bg-gray-800 block">
        <img
          src={thumbnailUrl}
          alt={video.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />
        {video.duration && (
          <span className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/80 text-white text-xs font-medium rounded">
            {formatDuration(video.duration)}
          </span>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      </Link>

      <div className="flex gap-3 mt-3">
        <Link href={`/channel/${video.channel.handle}`} className="flex-shrink-0">
          <div className="w-9 h-9 rounded-full bg-gray-600 overflow-hidden">
            {video.channel.avatar ? (
              <img src={video.channel.avatar} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="w-full h-full flex items-center justify-center text-sm text-white font-medium">
                {video.channel.name.charAt(0)}
              </span>
            )}
          </div>
        </Link>

        <div className="flex-1 min-w-0">
          <Link href={`/watch/${video.id}`}>
            <h3 className="text-white font-medium text-sm line-clamp-2 mb-1 group-hover:text-vidora-400 transition-colors leading-snug">
              {video.title}
            </h3>
          </Link>
          <Link href={`/channel/${video.channel.handle}`} className="text-xs text-gray-400 hover:text-gray-300 block">
            {video.channel.name}
            {video.channel.isVerified && <span className="ml-1">✓</span>}
          </Link>
          <p className="text-xs text-gray-400">
            {formatViews(video.viewCount)} views &middot; {formatRelativeTime(video.publishedAt || video.createdAt)}
          </p>
        </div>

        <div className="relative flex-shrink-0">
          <button
            onClick={(e) => { e.preventDefault(); setShowMenu(!showMenu); }}
            className="p-1.5 rounded-full opacity-0 group-hover:opacity-100 hover:bg-surface-dark-elevated transition-all text-gray-400"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {showMenu && (
            <>
              <div className="fixed inset-0 z-30" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-8 w-48 bg-surface-dark-elevated rounded-xl shadow-xl border border-gray-700 py-2 z-40 animate-fade-in">
                <button className="flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 w-full">
                  <Clock className="w-4 h-4" />
                  Watch Later
                </button>
                <button className="flex items-center gap-3 px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 w-full">
                  <ListPlus className="w-4 h-4" />
                  Save to Playlist
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function VideoCardSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="aspect-video rounded-xl bg-gray-800" />
      <div className="flex gap-3 mt-3">
        <div className="w-9 h-9 rounded-full bg-gray-800" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-800 rounded w-3/4" />
          <div className="h-3 bg-gray-800 rounded w-1/2" />
          <div className="h-3 bg-gray-800 rounded w-1/3" />
        </div>
      </div>
    </div>
  );
}
