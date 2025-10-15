import { createContext, useContext, useEffect, useState } from 'react';
import { surreal } from '../lib/surrealdb';
import { profileApi } from '../services/surrealdb';

import type { Profile as ProfileType } from '../lib/types';
type Profile = ProfileType;

interface AuthContextType {
  user: Profile | null;
  profile: Profile | null;
  loading: boolean;
  signUp: (email: string, password: string, username: string, displayName: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithSocial: (provider: string) => Promise<void>;
  sendPhoneOtp?: (phone: string) => Promise<void>;
  verifyPhoneOtp?: (phone: string, code: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Profile | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On mount, check for a stored token and user_id
    (async () => {
      try {
        const session = await supabase.auth.getSession();
        const userId = (localStorage.getItem('clipstream_user_id') || session?.data?.session?.user?.id) as string | null;
        if (userId) {
          await loadProfile(userId);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.warn('Failed to load profile from token', err);
        setLoading(false);
      }
    })();
  }, []);

  const loadProfile = async (userId: string) => {
    // Use the backend profileApi which is Surreal-backed
    const data: any = await profileApi.getProfile(userId);
    setProfile(data as Profile);
    setUser(data as Profile);
    setLoading(false);
  };

  const signUp = async (email: string, password: string, _username: string, _displayName: string) => {
    // Use supabase wrapper which calls our Surreal-backed register endpoint
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
    // Auto-login after register
    await signIn(email, password);
  };

  const signIn = async (email: string, password: string) => {
  const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  // supabase wrapper stores token/user_id in localStorage already
  const userId = localStorage.getItem('clipstream_user_id');
    if (!userId) throw new Error('Missing user id after login');
  await loadProfile(userId);
    setUser({ user_id: userId, email });
  };

  const signInWithSocial = async (provider: string) => {
    // Redirect to OAuth endpoint - the backend will handle the OAuth flow
    const redirectUrl = `${(import.meta as any).env.VITE_BACKEND_URL || (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8001'}/api/v1/auth/social/${provider}`;
    window.location.href = redirectUrl;
  };

  const sendPhoneOtp = async (phone: string) => {
    const apiBase = (import.meta as any).env.VITE_BACKEND_URL || (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8001';
    const res = await fetch(`${apiBase}/api/v1/auth/phone/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || 'Failed to send OTP');
    }
  };

  const verifyPhoneOtp = async (phone: string, code: string) => {
    const apiBase = (import.meta as any).env.VITE_BACKEND_URL || (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8001';
    const res = await fetch(`${apiBase}/api/v1/auth/phone/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, code }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || 'OTP verification failed');
    }
    const data = await res.json();
    const token = data.token;
    const userId = data.user_id;
    localStorage.setItem('clipstream_token', token);
    localStorage.setItem('clipstream_user_id', userId);
    await loadProfile(userId);
    setUser({ user_id: userId, email: '' });
  };

  const signOut = async () => {
    localStorage.removeItem('clipstream_token');
    localStorage.removeItem('clipstream_user_id');
    setUser(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider value={{ user, profile, loading, signUp, signIn, signInWithSocial, sendPhoneOtp, verifyPhoneOtp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
