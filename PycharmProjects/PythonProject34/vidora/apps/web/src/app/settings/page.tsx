'use client';

import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { useAuthStore } from '@/stores';
import { Monitor, Moon, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('dark');

  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-4 md:p-6">
        <h1 className="text-xl font-semibold text-white mb-6">Settings</h1>

        <div className="space-y-6">
          {/* Account */}
          <section className="bg-surface-dark-elevated rounded-xl p-6">
            <h2 className="text-lg font-medium text-white mb-4">Account</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Username</span>
                <span className="text-sm text-white">{user?.username}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Email</span>
                <span className="text-sm text-white">{user?.email}</span>
              </div>
            </div>
          </section>

          {/* Appearance */}
          <section className="bg-surface-dark-elevated rounded-xl p-6">
            <h2 className="text-lg font-medium text-white mb-4">Appearance</h2>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'light' as const, label: 'Light', icon: Sun },
                { value: 'dark' as const, label: 'Dark', icon: Moon },
                { value: 'system' as const, label: 'System', icon: Monitor },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTheme(option.value)}
                  className={cn(
                    'flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors',
                    theme === option.value
                      ? 'border-vidora-500 bg-vidora-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  )}
                >
                  <option.icon className="w-6 h-6 text-gray-300" />
                  <span className="text-sm text-gray-300">{option.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Privacy */}
          <section className="bg-surface-dark-elevated rounded-xl p-6">
            <h2 className="text-lg font-medium text-white mb-4">Privacy</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white">Search History</p>
                  <p className="text-xs text-gray-500">Save your search history</p>
                </div>
                <button className="w-11 h-6 bg-vidora-600 rounded-full relative">
                  <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5" />
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white">Notifications</p>
                  <p className="text-xs text-gray-500">Receive notifications</p>
                </div>
                <button className="w-11 h-6 bg-vidora-600 rounded-full relative">
                  <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5" />
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Layout>
  );
}
