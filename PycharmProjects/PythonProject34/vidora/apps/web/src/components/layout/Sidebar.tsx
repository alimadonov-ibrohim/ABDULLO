'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home, Compass, TrendingUp, Film, Users, Clock, PlaySquare,
  ThumbsUp, Library, Settings, HelpCircle, Info, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores';

const mainLinks = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/explore', label: 'Explore', icon: Compass },
  { href: '/trending', label: 'Trending', icon: TrendingUp },
  { href: '/shorts', label: 'Shorts', icon: Film },
  { href: '/subscriptions', label: 'Subscriptions', icon: Users },
];

const libraryLinks = [
  { href: '/library', label: 'Library', icon: Library },
  { href: '/history', label: 'History', icon: Clock },
  { href: '/watch-later', label: 'Watch Later', icon: PlaySquare },
  { href: '/liked', label: 'Liked Videos', icon: ThumbsUp },
];

const bottomLinks = [
  { href: '/settings', label: 'Settings', icon: Settings },
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/about', label: 'About', icon: Info },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const isCollapsed = !sidebarOpen;

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-[56px] bottom-0 z-40 bg-surface-dark overflow-y-auto transition-all duration-300',
          'scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent',
          isCollapsed ? 'w-[72px]' : 'w-[240px]',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <nav className="py-2 px-2">
          <div className="space-y-1">
            {mainLinks.map((link) => (
              <SidebarItem
                key={link.href}
                href={link.href}
                icon={link.icon}
                label={link.label}
                isActive={pathname === link.href}
                collapsed={isCollapsed}
              />
            ))}
          </div>

          {!isCollapsed && (
            <>
              <div className="my-3 mx-2 border-t border-gray-700" />

              <div className="space-y-1">
                <p className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Library
                </p>
                {libraryLinks.map((link) => (
                  <SidebarItem
                    key={link.href}
                    href={link.href}
                    icon={link.icon}
                    label={link.label}
                    isActive={pathname === link.href}
                    collapsed={isCollapsed}
                  />
                ))}
              </div>

              <div className="my-3 mx-2 border-t border-gray-700" />

              <div className="space-y-1">
                {bottomLinks.map((link) => (
                  <SidebarItem
                    key={link.href}
                    href={link.href}
                    icon={link.icon}
                    label={link.label}
                    isActive={pathname === link.href}
                    collapsed={isCollapsed}
                  />
                ))}
              </div>

              <div className="px-4 py-4 text-xs text-gray-500">
                <p>VIDORA Platform</p>
                <p className="mt-1">&copy; 2026 VIDORA</p>
              </div>
            </>
          )}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex absolute top-4 -right-3 w-6 h-6 bg-surface-dark-elevated rounded-full items-center justify-center border border-gray-600 hover:bg-gray-600 transition-colors"
        >
          {isCollapsed ? (
            <ChevronRight className="w-3 h-3 text-gray-400" />
          ) : (
            <ChevronLeft className="w-3 h-3 text-gray-400" />
          )}
        </button>
      </aside>
    </>
  );
}

function SidebarItem({
  href, icon: Icon, label, isActive, collapsed,
}: {
  href: string;
  icon: any;
  label: string;
  isActive: boolean;
  collapsed: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-4 px-3 py-2.5 rounded-xl text-sm transition-all duration-200',
        isActive
          ? 'bg-surface-dark-elevated text-white font-medium'
          : 'text-gray-400 hover:bg-surface-dark-elevated hover:text-white',
        collapsed && 'justify-center px-0',
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0', isActive && 'text-white')} />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
