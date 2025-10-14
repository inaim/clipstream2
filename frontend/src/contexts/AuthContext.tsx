import { createContext, useContext, useEffect, useState } from 'react';

type Profile = {
  user_id: string;
  email: string;
  display_name?: string;
};

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

  const API_BASE = import.meta.env.VITE_BACKEND_URL ||
                   import.meta.env.VITE_API_BASE_URL ||
                   'http://localhost:8001';

  useEffect(() => {
    // On mount, check for a stored token and user_id
    const token = localStorage.getItem('clipstream_token');
    const userId = localStorage.getItem('clipstream_user_id');
    if (token && userId) {
      // Load profile from API
      (async () => {
        try {
          await loadProfile(userId, token);
        } catch (err) {
          console.warn('Failed to load profile from token', err);
          setLoading(false);
        }
      })();
    } else {
      setLoading(false);
    }
  }, []);

  const loadProfile = async (userId: string, token?: string) => {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/v1/users/${userId}`, { headers });
    if (!res.ok) throw new Error('Failed to load profile');
    const data = await res.json();
    setProfile(data);
    setUser(data);
    setLoading(false);
  };

  const signUp = async (
    email: string,
    password: string,
    username: string,
    displayName: string
  ) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || 'Registration failed');
    }
    // Auto-login after successful registration (mock API doesn't return token on register)
    await signIn(email, password);
  };

  const signIn = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || 'Login failed');
    }
    const data = await res.json();
    const token = data.access_token;
    const userId = data.user_id;
    // store token locally
    localStorage.setItem('clipstream_token', token);
    localStorage.setItem('clipstream_user_id', userId);
    await loadProfile(userId, token);
    setUser({ user_id: userId, email });
  };

  const signInWithSocial = async (provider: string) => {
    // Redirect to OAuth endpoint - the backend will handle the OAuth flow
    const redirectUrl = `${API_BASE}/api/v1/auth/social/${provider}`;
    window.location.href = redirectUrl;
  };

  const sendPhoneOtp = async (phone: string) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/phone/send`, {
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
    const res = await fetch(`${API_BASE}/api/v1/auth/phone/verify`, {
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
    await loadProfile(userId, token);
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
