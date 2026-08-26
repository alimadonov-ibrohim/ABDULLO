'use client';

import { Layout } from '@/components/layout/Layout';
import { BarChart3 } from 'lucide-react';

export default function StudioAnalyticsPage() {
  return (
    <Layout>
      <div className="max-w-5xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Analytics</h1>
        <div className="bg-surface-dark-elevated rounded-xl p-12 text-center">
          <BarChart3 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Analytics will appear here once you have videos</p>
        </div>
      </div>
    </Layout>
  );
}
