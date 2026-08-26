'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores';
import { api } from '@/lib/api';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const token = searchParams.get('token');
    const refreshToken = searchParams.get('refreshToken');

    if (token && refreshToken) {
      api.setAccessToken(token);
      api.get('/auth/profile').then((user: any) => {
        setAuth(user, token, refreshToken);
        router.push('/');
      }).catch(() => {
        router.push('/auth/login');
      });
    } else {
      router.push('/auth/login');
    }
  }, [searchParams, setAuth, router]);

  return (
    <div className="min-h-screen bg-surface-dark flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-vidora-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
