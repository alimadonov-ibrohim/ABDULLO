export interface Comment {
  id: string;
  text: string;
  likeCount: number;
  replyCount: number;
  isDeleted: boolean;
  createdAt: Date;
  updatedAt: Date;
  userId: string;
  user: {
    id: string;
    username: string;
    avatar?: string | null;
    channel?: {
      id: string;
      name: string;
      avatar?: string | null;
      isVerified: boolean;
    };
  };
  videoId: string;
  parentId?: string | null;
  replies?: Comment[];
}

export interface CreateCommentDto {
  text: string;
  videoId: string;
  parentId?: string;
}

export interface UpdateCommentDto {
  text: string;
}
