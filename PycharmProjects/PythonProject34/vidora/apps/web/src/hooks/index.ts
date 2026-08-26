'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores';

export function useVideos(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['videos', params],
    queryFn: () => api.get('/videos', params),
  });
}

export function useTrendingVideos(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['videos', 'trending', params],
    queryFn: () => api.get('/videos/trending', params),
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: ['video', id],
    queryFn: () => api.get(`/videos/${id}`),
    enabled: !!id,
  });
}

export function useVideoRecommendations(videoId: string) {
  return useQuery({
    queryKey: ['recommendations', videoId],
    queryFn: () => api.get(`/recommendations/watch/${videoId}`),
    enabled: !!videoId,
  });
}

export function useHomeRecommendations() {
  return useQuery({
    queryKey: ['recommendations', 'home'],
    queryFn: () => api.get('/recommendations/home'),
  });
}

export function useChannel(channelId: string) {
  return useQuery({
    queryKey: ['channel', channelId],
    queryFn: () => api.get(`/channels/${channelId}`),
    enabled: !!channelId,
  });
}

export function useChannelVideos(channelId: string, params?: Record<string, any>) {
  return useQuery({
    queryKey: ['channel', channelId, 'videos', params],
    queryFn: () => api.get(`/channels/${channelId}/videos`, params),
    enabled: !!channelId,
  });
}

export function useSubscribe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (channelId: string) => api.post(`/channels/${channelId}/subscribe`),
    onSuccess: (_, channelId) => {
      queryClient.invalidateQueries({ queryKey: ['channel', channelId] });
    },
  });
}

export function useComments(videoId: string, params?: Record<string, any>) {
  return useQuery({
    queryKey: ['comments', videoId, params],
    queryFn: () => api.get(`/comments/video/${videoId}`, params),
    enabled: !!videoId,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { text: string; videoId: string; parentId?: string }) =>
      api.post('/comments', data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['comments', variables.videoId] });
    },
  });
}

export function useLikeVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ videoId, isLike }: { videoId: string; isLike: boolean }) =>
      api.post(`/videos/${videoId}/like`, { isLike }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['video', variables.videoId] });
    },
  });
}

export function useSearch(query: string, params?: Record<string, any>) {
  return useQuery({
    queryKey: ['search', query, params],
    queryFn: () => api.get('/search', { q: query, ...params }),
    enabled: !!query && query.length >= 2,
  });
}

export function useNotifications(params?: Record<string, any>) {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: ['notifications', params],
    queryFn: () => api.get('/notifications', params),
    enabled: isAuthenticated,
  });
}

export function useUnreadCount() {
  const { isAuthenticated } = useAuthStore();
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => api.get('/notifications/unread-count'),
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post('/auth/login', data),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: { email: string; username: string; password: string }) =>
      api.post('/auth/register', data),
  });
}

export function useWatchHistory(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['videos', 'history', params],
    queryFn: () => api.get('/videos/history', params),
  });
}

export function useWatchLater(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['videos', 'watch-later', params],
    queryFn: () => api.get('/videos/watch-later', params),
  });
}

export function useLikedVideos(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['videos', 'liked', params],
    queryFn: () => api.get('/videos/liked', params),
  });
}

export function useMyPlaylists() {
  return useQuery({
    queryKey: ['playlists', 'me'],
    queryFn: () => api.get('/playlists/me'),
  });
}
