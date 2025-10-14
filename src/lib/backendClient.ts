// Minimal backend adapter to provide a supabase-like API for the frontend
const API_BASE = (import.meta as any).env.VITE_BACKEND_URL || 'http://localhost:8000';

async function json(res: Response) {
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || 'Request failed');
  }
  return res.json();
}

class BackendQuery {
  table: string;
  filters: Record<string, any> = {};
  constructor(table: string) {
    this.table = table;
  }
  select(_cols?: string) {
    return this;
  }
  eq(field: string, value: any) {
    this.filters[field] = value;
    return this;
  }
  async maybeSingle() {
    if (this.table === 'likes') {
      const params = new URLSearchParams();
      if (this.filters['user_id']) params.append('user_id', String(this.filters['user_id']));
      if (this.filters['video_id']) params.append('video_id', String(this.filters['video_id']));
      const res = await fetch(`${API_BASE}/api/likes?${params.toString()}`);
      return { data: (await json(res)).data, error: null };
    }
    if (this.table === 'follows') {
      const params = new URLSearchParams();
      if (this.filters['follower_id']) params.append('follower_id', String(this.filters['follower_id']));
      if (this.filters['following_id']) params.append('following_id', String(this.filters['following_id']));
      const res = await fetch(`${API_BASE}/api/follows?${params.toString()}`);
      return { data: (await json(res)).data, error: null };
    }
    return { data: null, error: null };
  }
  async insert(row: any) {
    if (this.table === 'likes') {
      const res = await fetch(`${API_BASE}/api/likes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(row) });
      return { data: await json(res), error: null };
    }
    if (this.table === 'follows') {
      const res = await fetch(`${API_BASE}/api/follows`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(row) });
      return { data: await json(res), error: null };
    }
    if (this.table === 'comments') {
      const res = await fetch(`${API_BASE}/api/comments`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(row) });
      return { data: await json(res), error: null };
    }
    return { data: null, error: null };
  }
  async delete() {
    if (this.table === 'likes') {
      const res = await fetch(`${API_BASE}/api/likes`, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.filters) });
      return { data: await json(res), error: null };
    }
    if (this.table === 'follows') {
      const res = await fetch(`${API_BASE}/api/follows`, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.filters) });
      return { data: await json(res), error: null };
    }
    return { data: null, error: null };
  }
}

export const backendClient = {
  from: (table: string) => new BackendQuery(table),
  storage: {
    from: (_bucket: string) => ({
      upload: async () => ({ error: null }),
      getPublicUrl: (_path: string) => ({ data: { publicUrl: '' } }),
    }),
  },
  auth: {
    signUp: async ({ email, password }: { email: string; password: string }) => {
      const res = await fetch(`${API_BASE}/api/v1/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
      return { data: await json(res), error: null };
    },
    signInWithPassword: async ({ email, password }: { email: string; password: string }) => {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
      return { data: await json(res), error: null };
    },
    signOut: async () => ({ error: null }),
  },
  __backend: true,
};

export default backendClient;
