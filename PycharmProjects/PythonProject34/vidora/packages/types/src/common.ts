export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  errorCode?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: {
    items: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

export interface PaginationQuery {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export type VideoStatus = 'UPLOADING' | 'PROCESSING' | 'READY' | 'FAILED';
export type VideoVisibility = 'PUBLIC' | 'UNLISTED' | 'PRIVATE';
export type UserRole = 'USER' | 'CREATOR' | 'MODERATOR' | 'ADMIN' | 'SUPER_ADMIN';
export type ReportStatus = 'PENDING' | 'REVIEWING' | 'RESOLVED' | 'REJECTED';
export type ReportReason = 'SPAM' | 'MISLEADING' | 'HARASSMENT' | 'COPYRIGHT' | 'DANGEROUS_CONTENT' | 'OTHER';
export type NotificationType = 'SUBSCRIPTION' | 'COMMENT' | 'COMMENT_REPLY' | 'LIKE' | 'NEW_VIDEO' | 'MENTION';
