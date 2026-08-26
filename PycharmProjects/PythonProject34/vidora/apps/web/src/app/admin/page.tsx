'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { useAuthStore } from '@/stores';
import { api } from '@/lib/api';
import { Users, Video, Eye, MessageSquare, AlertTriangle, Settings, BarChart3 } from 'lucide-react';

export default function AdminPage() {
  const { user, isAuthenticated, hasRole } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && hasRole(['ADMIN', 'SUPER_ADMIN'])) {
      api.get('/admin/dashboard')
        .then(setStats)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, hasRole]);

  if (!isAuthenticated || !hasRole(['ADMIN', 'SUPER_ADMIN'])) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-gray-400">Access denied. Admin only.</p>
        </div>
      </Layout>
    );
  }

  const statCards = stats ? [
    { label: 'Total Users', value: stats.totalUsers, icon: Users, color: 'blue' },
    { label: 'Active Users', value: stats.activeUsers, icon: Users, color: 'green' },
    { label: 'Total Videos', value: stats.totalVideos, icon: Video, color: 'purple' },
    { label: 'Total Views', value: stats.totalViews?.toLocaleString(), icon: Eye, color: 'yellow' },
    { label: 'Total Comments', value: stats.totalComments, icon: MessageSquare, color: 'pink' },
    { label: 'Pending Reports', value: stats.pendingReports, icon: AlertTriangle, color: 'red' },
    { label: 'Processing Jobs', value: stats.processingJobs, icon: Settings, color: 'orange' },
  ] : [];

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Admin Dashboard</h1>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-32 bg-surface-dark-elevated rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {statCards.map((stat) => (
                <div key={stat.label} className="bg-surface-dark-elevated rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <stat.icon className="w-5 h-5 text-gray-400" />
                    <span className="text-xs text-gray-500">{stat.label}</span>
                  </div>
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Link href="/admin/users" className="bg-surface-dark-elevated rounded-xl p-6 hover:bg-gray-700 transition-colors">
                <Users className="w-8 h-8 text-blue-500 mb-3" />
                <h3 className="text-white font-medium">Manage Users</h3>
                <p className="text-sm text-gray-400 mt-1">View and manage user accounts</p>
              </Link>
              <Link href="/admin/videos" className="bg-surface-dark-elevated rounded-xl p-6 hover:bg-gray-700 transition-colors">
                <Video className="w-8 h-8 text-purple-500 mb-3" />
                <h3 className="text-white font-medium">Manage Videos</h3>
                <p className="text-sm text-gray-400 mt-1">Review and moderate videos</p>
              </Link>
              <Link href="/admin/reports" className="bg-surface-dark-elevated rounded-xl p-6 hover:bg-gray-700 transition-colors">
                <AlertTriangle className="w-8 h-8 text-red-500 mb-3" />
                <h3 className="text-white font-medium">Reports</h3>
                <p className="text-sm text-gray-400 mt-1">Handle user reports</p>
              </Link>
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
