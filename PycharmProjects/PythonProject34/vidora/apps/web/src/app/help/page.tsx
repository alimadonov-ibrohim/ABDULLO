'use client';

import { Layout } from '@/components/layout/Layout';
import { HelpCircle } from 'lucide-react';

export default function HelpPage() {
  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Help Center</h1>
        <div className="bg-surface-dark-elevated rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <HelpCircle className="w-6 h-6 text-vidora-500" />
            <h2 className="text-lg font-medium text-white">Need Help?</h2>
          </div>
          <p className="text-gray-400">
            If you need assistance, please contact our support team at support@vidora.com
          </p>
        </div>
      </div>
    </Layout>
  );
}
