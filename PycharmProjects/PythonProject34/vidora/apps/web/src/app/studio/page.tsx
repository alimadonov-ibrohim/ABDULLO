'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Video, Upload, BarChart3, MessageSquare, Settings,
  PlaySquare, ChevronRight,
} from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { useAuthStore } from '@/stores';
import { cn } from '@/lib/utils';

const studioLinks = [
  { href: '/studio/videos', label: 'Videos', icon: Video, description: 'Manage your videos' },
  { href: '/studio/analytics', label: 'Analytics', icon: BarChart3, description: 'View channel analytics' },
  { href: '/studio/comments', label: 'Comments', icon: MessageSquare, description: 'Manage comments' },
  { href: '/studio/settings', label: 'Settings', icon: Settings, description: 'Channel settings' },
];

export default function StudioPage() {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-gray-400 mb-4">Sign in to access Creator Studio</p>
          <Link href="/auth/login" className="px-6 py-2 bg-vidora-600 text-white rounded-full hover:bg-vidora-500 transition-colors">
            Sign In
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto p-4 md:p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-white">Creator Studio</h1>
          <Link
            href="/studio/videos"
            className="flex items-center gap-2 px-4 py-2 bg-vidora-600 text-white rounded-full hover:bg-vidora-500 transition-colors text-sm font-medium"
          >
            <Upload className="w-4 h-4" />
            Upload Video
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {studioLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="flex items-center gap-4 p-6 bg-surface-dark-elevated rounded-xl hover:bg-gray-700 transition-colors group"
            >
              <div className="w-12 h-12 rounded-xl bg-vidora-600/20 flex items-center justify-center group-hover:bg-vidora-600/30 transition-colors">
                <link.icon className="w-6 h-6 text-vidora-500" />
              </div>
              <div className="flex-1">
                <p className="text-white font-medium">{link.label}</p>
                <p className="text-sm text-gray-400">{link.description}</p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-gray-300 transition-colors" />
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
