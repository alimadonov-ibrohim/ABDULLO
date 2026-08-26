'use client';

import Link from 'next/link';
import { Clock, PlaySquare, ThumbsUp, ListVideo, History } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { useWatchHistory, useWatchLater, useLikedVideos, useMyPlaylists } from '@/hooks';
import { useAuthStore } from '@/stores';

const sections = [
  { href: '/history', label: 'History', icon: History },
  { href: '/watch-later', label: 'Watch Later', icon: Clock },
  { href: '/liked', label: 'Liked Videos', icon: ThumbsUp },
];

export default function LibraryPage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Layout>
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Library</h1>

        {!isAuthenticated ? (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-gray-400 mb-4">Sign in to access your library</p>
            <Link
              href="/auth/login"
              className="px-6 py-2 bg-vidora-600 text-white rounded-full hover:bg-vidora-500 transition-colors"
            >
              Sign In
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sections.map((section) => (
              <Link
                key={section.href}
                href={section.href}
                className="flex items-center gap-4 p-6 bg-surface-dark-elevated rounded-xl hover:bg-gray-700 transition-colors group"
              >
                <div className="w-12 h-12 rounded-xl bg-vidora-600/20 flex items-center justify-center group-hover:bg-vidora-600/30 transition-colors">
                  <section.icon className="w-6 h-6 text-vidora-500" />
                </div>
                <div>
                  <p className="text-white font-medium">{section.label}</p>
                  <p className="text-sm text-gray-400">View all</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
