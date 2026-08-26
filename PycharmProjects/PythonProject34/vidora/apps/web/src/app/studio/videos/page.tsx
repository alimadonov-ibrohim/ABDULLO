'use client';

import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Upload, Video, Clock, CheckCircle, XCircle } from 'lucide-react';
import { useAuthStore } from '@/stores';
import Link from 'next/link';

export default function StudioVideosPage() {
  const { isAuthenticated } = useAuthStore();
  const [showUpload, setShowUpload] = useState(false);

  if (!isAuthenticated) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-gray-400 mb-4">Sign in to manage videos</p>
          <Link href="/auth/login" className="px-6 py-2 bg-vidora-600 text-white rounded-full">Sign In</Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto p-4 md:p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-white">Video Management</h1>
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-vidora-600 text-white rounded-full hover:bg-vidora-500 transition-colors text-sm font-medium"
          >
            <Upload className="w-4 h-4" />
            Upload Video
          </button>
        </div>

        {showUpload && (
          <div className="mb-6 bg-surface-dark-elevated rounded-xl p-6">
            <h2 className="text-lg font-medium text-white mb-4">Upload Video</h2>
            <div className="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center hover:border-vidora-500 transition-colors cursor-pointer">
              <Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400 mb-2">Drag and drop video files or click to browse</p>
              <p className="text-xs text-gray-600">Supports MP4, AVI, MOV, WebM (max 10GB)</p>
            </div>
            <div className="mt-4 space-y-3">
              <input
                type="text"
                placeholder="Video title"
                className="w-full h-10 px-4 bg-surface-dark border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-vidora-500"
              />
              <textarea
                placeholder="Description"
                rows={3}
                className="w-full px-4 py-2 bg-surface-dark border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-vidora-500 resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowUpload(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button className="px-6 py-2 bg-vidora-600 text-white rounded-full hover:bg-vidora-500 transition-colors text-sm font-medium">
                  Upload
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="bg-surface-dark-elevated rounded-xl p-12 text-center">
          <Video className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No videos uploaded yet</p>
          <p className="text-sm text-gray-500 mt-1">Click "Upload Video" to get started</p>
        </div>
      </div>
    </Layout>
  );
}
