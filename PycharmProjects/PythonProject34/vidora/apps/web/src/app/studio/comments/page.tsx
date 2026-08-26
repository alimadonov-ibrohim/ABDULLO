'use client';

import { Layout } from '@/components/layout/Layout';
import { MessageSquare } from 'lucide-react';

export default function StudioCommentsPage() {
  return (
    <Layout>
      <div className="max-w-5xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Comment Management</h1>
        <div className="bg-surface-dark-elevated rounded-xl p-12 text-center">
          <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No comments to manage</p>
        </div>
      </div>
    </Layout>
  );
}
