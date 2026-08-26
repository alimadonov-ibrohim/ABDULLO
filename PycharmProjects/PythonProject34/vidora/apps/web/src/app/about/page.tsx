'use client';

import { Layout } from '@/components/layout/Layout';
import { Video } from 'lucide-react';

export default function AboutPage() {
  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">About VIDORA</h1>
        <div className="bg-surface-dark-elevated rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-vidora-600 rounded-lg flex items-center justify-center">
              <Video className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-lg font-medium text-white">VIDORA Platform</h2>
          </div>
          <p className="text-gray-400">
            VIDORA is a modern video sharing platform built with cutting-edge technology.
            Share, discover, and enjoy videos from creators around the world.
          </p>
          <p className="text-sm text-gray-500">Version 1.0.0</p>
        </div>
      </div>
    </Layout>
  );
}
