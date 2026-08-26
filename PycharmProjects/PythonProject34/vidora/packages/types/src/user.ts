export interface User {
  id: string;
  email: string;
  username: string;
  avatar?: string | null;
  banner?: string | null;
  description?: string | null;
  role: string;
  isVerified: boolean;
  isEmailVerified: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserProfile extends User {
  channel?: {
    id: string;
    name: string;
    handle: string;
    subscriberCount: number;
    videoCount: number;
    avatar?: string | null;
    isVerified: boolean;
  };
  _count?: {
    subscriptions: number;
  };
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface LoginDto {
  email: string;
  password: string;
}

export interface RegisterDto {
  email: string;
  username: string;
  password: string;
  dateOfBirth?: string;
}
