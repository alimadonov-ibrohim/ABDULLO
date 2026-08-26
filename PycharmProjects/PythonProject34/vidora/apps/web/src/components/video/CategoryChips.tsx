'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';

const categories = [
  'All', 'Music', 'Gaming', 'Programming', 'News', 'Education',
  'Sports', 'Movies', 'Technology', 'Live', 'Comedy', 'Travel',
  'Science', 'Cooking', 'Fitness', 'Art',
];

interface CategoryChipsProps {
  selected?: string;
  onSelect: (category: string) => void;
}

export function CategoryChips({ selected = 'All', onSelect }: CategoryChipsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto py-3 px-4 scrollbar-none">
      {categories.map((category) => (
        <button
          key={category}
          onClick={() => onSelect(category)}
          className={cn(
            'px-4 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200',
            selected === category
              ? 'bg-white text-black'
              : 'bg-surface-dark-elevated text-gray-300 hover:bg-gray-600',
          )}
        >
          {category}
        </button>
      ))}
    </div>
  );
}
