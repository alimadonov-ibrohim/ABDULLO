'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ThumbsUp, ThumbsDown, Share2, Download, MoreHorizontal,
  Plus, MessageSquare, ChevronDown, ChevronUp,
} from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { VideoCard } from '@/components/video/VideoCard';
import { cn, formatViews, formatRelativeTime, formatDuration } from '@/lib/utils';
import { useVideo, useVideoRecommendations, useComments, useLikeVideo, useCreateComment, useSubscribe } from '@/hooks';
import { useAuthStore } from '@/stores';

export default function WatchPage() {
  const params = useParams();
  const videoId = params.videoId as string;
  const { user, isAuthenticated } = useAuthStore();

  const { data: video, isLoading } = useVideo(videoId);
  const { data: recommendations } = useVideoRecommendations(videoId);
  const { data: commentsData, isLoading: commentsLoading } = useComments(videoId);
  const likeMutation = useLikeVideo();
  const createCommentMutation = useCreateComment();
  const subscribeMutation = useSubscribe();

  const [commentText, setCommentText] = useState('');
  const [showDescription, setShowDescription] = useState(false);
  const [sortBy, setSortBy] = useState('newest');

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-vidora-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </Layout>
    );
  }

  if (!video) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-20">
          <p className="text-gray-400 text-lg">Video not found</p>
        </div>
      </Layout>
    );
  }

  const handleLike = (isLike: boolean) => {
    if (!isAuthenticated) return;
    likeMutation.mutate({ videoId, isLike });
  };

  const handleComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !isAuthenticated) return;
    createCommentMutation.mutate(
      { text: commentText, videoId },
      { onSuccess: () => setCommentText('') }
    );
  };

  const handleSubscribe = () => {
    if (!isAuthenticated) return;
    subscribeMutation.mutate(video.channel.id);
  };

  return (
    <Layout>
      <div className="max-w-[1800px] mx-auto flex flex-col lg:flex-row gap-6 p-4 md:p-6">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Video Player */}
          <div className="aspect-video bg-black rounded-xl overflow-hidden">
            {video.hlsUrl ? (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <p>HLS Player - {video.title}</p>
              </div>
            ) : video.videoUrl ? (
              <video
                src={video.videoUrl}
                controls
                className="w-full h-full"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <p>Video not available</p>
              </div>
            )}
          </div>

          {/* Title */}
          <h1 className="text-xl font-semibold text-white mt-4">{video.title}</h1>

          {/* Channel info & actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-3">
            <Link href={`/channel/${video.channel.handle}`} className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gray-600 overflow-hidden flex-shrink-0">
                {video.channel.avatar ? (
                  <img src={video.channel.avatar} alt="" className="w-full h-full object-cover" />
                ) : (
                  <span className="w-full h-full flex items-center justify-center text-sm text-white font-medium">
                    {video.channel.name.charAt(0)}
                  </span>
                )}
              </div>
              <div>
                <p className="text-white font-medium text-sm flex items-center gap-1">
                  {video.channel.name}
                  {video.channel.isVerified && <span className="text-gray-400 text-xs">✓</span>}
                </p>
                <p className="text-xs text-gray-400">
                  {video.channel.subscriberCount?.toLocaleString()} subscribers
                </p>
              </div>
              <button
                onClick={handleSubscribe}
                className={cn(
                  'ml-4 px-4 py-2 rounded-full text-sm font-medium transition-colors',
                  subscribeMutation.data?.subscribed
                    ? 'bg-gray-600 text-white hover:bg-gray-500'
                    : 'bg-white text-black hover:bg-gray-200'
                )}
              >
                {subscribeMutation.data?.subscribed ? 'Subscribed' : 'Subscribe'}
              </button>
            </Link>

            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center bg-surface-dark-elevated rounded-full">
                <button
                  onClick={() => handleLike(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-l-full hover:bg-gray-600 transition-colors text-sm"
                >
                  <ThumbsUp className="w-4 h-4" />
                  <span>{video.likeCount?.toLocaleString()}</span>
                </button>
                <div className="w-px h-6 bg-gray-600" />
                <button
                  onClick={() => handleLike(false)}
                  className="p-2 rounded-r-full hover:bg-gray-600 transition-colors"
                >
                  <ThumbsDown className="w-4 h-4" />
                </button>
              </div>
              <button className="flex items-center gap-2 px-4 py-2 bg-surface-dark-elevated rounded-full hover:bg-gray-600 transition-colors text-sm">
                <Share2 className="w-4 h-4" />
                <span className="hidden sm:inline">Share</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-surface-dark-elevated rounded-full hover:bg-gray-600 transition-colors text-sm">
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">Download</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-surface-dark-elevated rounded-full hover:bg-gray-600 transition-colors text-sm">
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">Save</span>
              </button>
            </div>
          </div>

          {/* Description */}
          <div
            className="mt-4 p-3 bg-surface-dark-elevated rounded-xl cursor-pointer hover:bg-gray-700 transition-colors"
            onClick={() => setShowDescription(!showDescription)}
          >
            <div className="flex items-center gap-2 text-sm text-gray-300 mb-1">
              <span>{formatViews(video.viewCount)} views</span>
              <span>&middot;</span>
              <span>{formatRelativeTime(video.publishedAt || video.createdAt)}</span>
            </div>
            {video.description && (
              <p className={cn('text-sm text-gray-300 whitespace-pre-wrap', !showDescription && 'line-clamp-3')}>
                {video.description}
              </p>
            )}
            {video.description && video.description.length > 200 && (
              <button className="text-sm text-gray-400 font-medium mt-1">
                {showDescription ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>

          {/* Comments */}
          <div className="mt-6">
            <div className="flex items-center gap-6 mb-4">
              <h3 className="text-white font-medium">
                {video.commentCount || 0} Comments
              </h3>
              <button
                onClick={() => setSortBy(sortBy === 'newest' ? 'top' : 'newest')}
                className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
              >
                Sort by: {sortBy === 'newest' ? 'Newest first' : 'Top comments'}
              </button>
            </div>

            {/* Comment input */}
            {isAuthenticated && (
              <form onSubmit={handleComment} className="flex gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-vidora-600 flex-shrink-0 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">
                    {user?.username?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1">
                  <input
                    type="text"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Add a comment..."
                    className="w-full bg-transparent border-b border-gray-600 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-white transition-colors"
                  />
                  {commentText.trim() && (
                    <div className="flex justify-end gap-2 mt-2">
                      <button
                        type="button"
                        onClick={() => setCommentText('')}
                        className="px-3 py-1.5 text-sm text-gray-400 hover:text-white"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-1.5 bg-vidora-600 text-white text-sm font-medium rounded-full hover:bg-vidora-500 transition-colors"
                      >
                        Comment
                      </button>
                    </div>
                  )}
                </div>
              </form>
            )}

            {/* Comments list */}
            <div className="space-y-4">
              {commentsLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex gap-3 animate-pulse">
                    <div className="w-10 h-10 rounded-full bg-gray-800" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-gray-800 rounded w-1/4" />
                      <div className="h-4 bg-gray-800 rounded w-3/4" />
                    </div>
                  </div>
                ))
              ) : commentsData?.items?.length > 0 ? (
                commentsData.items.map((comment: any) => (
                  <div key={comment.id} className="flex gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-600 flex-shrink-0 overflow-hidden">
                      {comment.user?.avatar ? (
                        <img src={comment.user.avatar} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <span className="w-full h-full flex items-center justify-center text-sm text-white font-medium">
                          {comment.user?.username?.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-300">
                          {comment.user?.username}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatRelativeTime(comment.createdAt)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-200 mt-1">{comment.text}</p>
                      <div className="flex items-center gap-4 mt-2">
                        <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300">
                          <ThumbsUp className="w-3 h-3" />
                          {comment.likeCount > 0 && comment.likeCount}
                        </button>
                        <button className="text-xs text-gray-500 hover:text-gray-300">Reply</button>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-8">No comments yet</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar - Recommendations */}
        <div className="w-full lg:w-[400px] xl:w-[450px] flex-shrink-0">
          <h3 className="text-white font-medium mb-4">Recommended</h3>
          <div className="space-y-3">
            {recommendations?.items?.map((rec: any) => (
              <Link
                key={rec.id}
                href={`/watch/${rec.id}`}
                className="flex gap-2 group"
              >
                <div className="w-[168px] aspect-video rounded-lg overflow-hidden bg-gray-800 flex-shrink-0 relative">
                  {rec.thumbnailUrl ? (
                    <img
                      src={rec.thumbnailUrl}
                      alt={rec.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full" />
                  )}
                  {rec.duration && (
                    <span className="absolute bottom-1 right-1 px-1 py-0.5 bg-black/80 text-white text-[10px] rounded">
                      {formatDuration(rec.duration)}
                    </span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm text-white font-medium line-clamp-2 group-hover:text-vidora-400 transition-colors">
                    {rec.title}
                  </h4>
                  <p className="text-xs text-gray-400 mt-1">{rec.channel?.name}</p>
                  <p className="text-xs text-gray-400">
                    {formatViews(rec.viewCount)} views
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
