'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Video, Mail, Lock, User } from 'lucide-react';
import { useLogin } from '@/hooks';
import { useAuthStore } from '@/stores';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const loginMutation = useLogin();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const result = await loginMutation.mutateAsync({ email, password });
      setAuth(result.user, result.accessToken, result.refreshToken);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-surface-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-vidora-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <Video className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Welcome to VIDORA</h1>
          <p className="text-gray-400 mt-2">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full h-10 pl-10 pr-4 bg-surface-dark-elevated border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-vidora-500 transition-colors"
                placeholder="Enter your email"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full h-10 pl-10 pr-4 bg-surface-dark-elevated border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-vidora-500 transition-colors"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full h-10 bg-vidora-600 text-white font-medium rounded-lg hover:bg-vidora-500 transition-colors disabled:opacity-50"
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-surface-dark text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL}/api/auth/google`}
              className="flex items-center justify-center gap-2 h-10 bg-surface-dark-elevated border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-600 transition-colors text-sm"
            >
              Google
            </a>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL}/api/auth/github`}
              className="flex items-center justify-center gap-2 h-10 bg-surface-dark-elevated border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-600 transition-colors text-sm"
            >
              GitHub
            </a>
          </div>
        </div>

        <p className="text-center text-sm text-gray-400 mt-6">
          Don&apos;t have an account?{' '}
          <Link href="/auth/register" className="text-vidora-500 hover:underline">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  );
}
