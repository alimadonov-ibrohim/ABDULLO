'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Search, Menu, Bell, Plus, User, LogOut, Settings, Video,
  ChevronDown, Mic,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore, useUIStore } from '@/stores';
import { useUnreadCount } from '@/hooks';

export function Navbar() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { user, isAuthenticated, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();
  const { data: unreadData } = useUnreadCount();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    router.push('/');
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-[56px] bg-surface-dark z-50 flex items-center justify-between px-4 gap-4">
      {/* Left */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-full hover:bg-surface-dark-elevated transition-colors text-white"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link href="/" className="flex items-center gap-1">
          <div className="w-8 h-8 bg-vidora-600 rounded-lg flex items-center justify-center">
            <Video className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-white tracking-tight hidden sm:block">
            VIDORA
          </span>
        </Link>
      </div>

      {/* Center - Search */}
      <div className="flex-1 max-w-2xl mx-auto">
        <form onSubmit={handleSearch} className="flex items-center">
          <div className="flex-1 flex">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search videos..."
              className="w-full h-10 pl-4 pr-2 bg-surface-dark border border-gray-600 rounded-l-full text-white placeholder-gray-400 focus:outline-none focus:border-vidora-500 transition-colors"
            />
            <button
              type="submit"
              className="h-10 px-5 bg-surface-dark-elevated border border-l-0 border-gray-600 rounded-r-full hover:bg-gray-600 transition-colors"
            >
              <Search className="w-5 h-5 text-gray-300" />
            </button>
          </div>
          <button
            type="button"
            className="ml-2 p-2.5 bg-surface-dark-elevated rounded-full hover:bg-gray-600 transition-colors hidden sm:flex"
          >
            <Mic className="w-5 h-5 text-gray-300" />
          </button>
        </form>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {isAuthenticated ? (
          <>
            {/* Create button */}
            <Link
              href="/studio"
              className="flex items-center gap-2 px-3 py-2 rounded-full hover:bg-surface-dark-elevated transition-colors text-white hidden sm:flex"
            >
              <Plus className="w-5 h-5" />
              <span className="text-sm">Create</span>
            </Link>

            {/* Notifications */}
            <Link
              href="/notifications"
              className="relative p-2 rounded-full hover:bg-surface-dark-elevated transition-colors text-white"
            >
              <Bell className="w-5 h-5" />
              {unreadData && unreadData.count > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] font-bold flex items-center justify-center text-white">
                  {unreadData.count > 99 ? '99+' : unreadData.count}
                </span>
              )}
            </Link>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 p-1 rounded-full hover:bg-surface-dark-elevated transition-colors"
              >
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.username}
                    className="w-8 h-8 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-8 h-8 bg-vidora-600 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.username?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
              </button>

              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 top-12 w-60 bg-surface-dark-elevated rounded-xl shadow-xl border border-gray-700 py-2 z-50 animate-fade-in">
                    <div className="px-4 py-3 border-b border-gray-700">
                      <p className="text-sm font-medium text-white">{user?.username}</p>
                      <p className="text-xs text-gray-400">{user?.email}</p>
                    </div>
                    <Link
                      href={`/channel/${user?.channel?.handle || ''}`}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <User className="w-4 h-4" />
                      Your Channel
                    </Link>
                    <Link
                      href="/studio"
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Video className="w-4 h-4" />
                      Creator Studio
                    </Link>
                    <Link
                      href="/settings"
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </Link>
                    <div className="border-t border-gray-700 mt-1 pt-1">
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors w-full"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </>
        ) : (
          <Link
            href="/auth/login"
            className="flex items-center gap-2 px-4 py-2 border border-vidora-500 rounded-full text-vidora-500 hover:bg-vidora-500/10 transition-colors text-sm font-medium"
          >
            <User className="w-4 h-4" />
            Sign In
          </Link>
        )}
      </div>
    </header>
  );
}
