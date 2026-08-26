'use client';

import { Layout } from '@/components/layout/Layout';
import { Film } from 'lucide-react';

export default function ShortsPage() {
  return (
    <Layout>
      <div className="flex flex-col items-center justify-center py-20">
        <Film className="w-16 h-16 text-gray-600 mb-4" />
        <h1 className="text-xl font-semibold text-white mb-2">Shorts</h1>
        <p className="text-gray-400">Short videos coming soon</p>
      </div>
    </Layout>
  );
}
