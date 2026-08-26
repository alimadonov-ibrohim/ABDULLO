'use client';

import { Layout } from '@/components/layout/Layout';
import { useNotifications } from '@/hooks';
import { useAuthStore } from '@/stores';
import Link from 'next/link';
import { Bell } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';

export default function NotificationsPage() {
  const { isAuthenticated } = useAuthStore();
  const { data, isLoading } = useNotifications({ limit: 50 });

  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-4">Notifications</h1>

        {!isAuthenticated ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Bell className="w-12 h-12 text-gray-600 mb-4" />
            <p className="text-gray-400 mb-4">Sign in to view notifications</p>
          </div>
        ) : isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-surface-dark-elevated rounded-xl animate-pulse">
                <div className="w-10 h-10 rounded-full bg-gray-700" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-700 rounded w-3/4" />
                  <div className="h-3 bg-gray-700 rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.items?.length > 0 ? (
          <div className="space-y-1">
            {data.items.map((notification: any) => (
              <Link
                key={notification.id}
                href={notification.link || '#'}
                className={`flex items-center gap-4 p-4 rounded-xl hover:bg-surface-dark-elevated transition-colors ${
                  !notification.isRead ? 'bg-surface-dark-elevated/50' : ''
                }`}
              >
                <div className="w-10 h-10 rounded-full bg-gray-600 overflow-hidden flex-shrink-0">
                  {notification.sender?.avatar ? (
                    <img src={notification.sender.avatar} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <span className="w-full h-full flex items-center justify-center text-sm text-white font-medium">
                      {notification.sender?.username?.charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200">
                    <span className="font-medium">{notification.sender?.username}</span>
                    {' '}{notification.message}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatRelativeTime(notification.createdAt)}
                  </p>
                </div>
                {!notification.isRead && (
                  <div className="w-2 h-2 bg-vidora-500 rounded-full flex-shrink-0" />
                )}
              </Link>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20">
            <Bell className="w-12 h-12 text-gray-600 mb-4" />
            <p className="text-gray-400">No notifications yet</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
