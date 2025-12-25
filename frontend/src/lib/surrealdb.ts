/**
 * Supabase compatibility layer
 * This file provides a Supabase-like interface that calls our SurrealDB backend
 * This allows us to migrate from Supabase to SurrealDB without changing all component code
 */
import { profileApi, videoApi, socialApi } from '../services/surrealdb';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
                     'http://localhost:8080';

// auth headers and network helpers live in `src/services/surrealdb.ts` for the explicit API layer

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Supabase-compatible wrapper for SurrealDB backend
 * Provides the same interface as Supabase for easy migration
 */

type Row = Record<string, any>;

class QueryBuilder implements PromiseLike<any> {
  table: string;
  filters: Record<string, any> = {};
  _selectCols?: string;
  _selectOptions?: any;
  _limit?: number;
  _offset?: number;
  _order?: { field: string; opts?: any } | null = null;

  constructor(table: string) {
    this.table = table;
  }

  select(cols?: string, opts?: any) {
    this._selectCols = cols;
    this._selectOptions = opts;
    return this;
  }

  limit(n: number) {
    this._limit = n;
    return this;
  }

  offset(n: number) {
    this._offset = n;
    return this;
  }

  order(field: string, opts?: any) {
    this._order = { field, opts };
    return this;
  }

  is(field: string, value: any) {
    // convenience for is(null) used in comments
    this.filters[field] = value;
    return this;
  }

  eq(field: string, value: any) {
    this.filters[field] = value;
    return this;
  }

  async maybeSingle() {
    try {
      // Map table names to API endpoints
      if (this.table === 'profiles' && this.filters.id) {
        const data = await profileApi.getProfile(this.filters.id);
        return { data, error: null };
      }
      if (this.table === 'videos' && this.filters.id) {
        const data = await videoApi.getVideo(this.filters.id);
        return { data, error: null };
      }
      return { data: null, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  async insert(records: Row | Row[]) {
    try {
      const arr = Array.isArray(records) ? records : [records];
      // Handle different table types
      if (this.table === 'likes') {
        for (const record of arr) {
          await socialApi.likeVideo(record.user_id, record.video_id);
        }
      } else if (this.table === 'follows') {
        for (const record of arr) {
          await socialApi.followUser(record.follower_id, record.following_id);
        }
      } else if (this.table === 'comments') {
        for (const record of arr) {
          await socialApi.postComment(record.video_id, record.user_id, record.content, record.parent_id);
        }
      }
      return { data: arr, error: null };
    } catch (error) {
      return { data: null, error };
    }
  }

  update(updates: Row) {
    // Return an object that supports .eq(field, value) chaining
    const self = this;
    return {
      eq: async (field: string, value: any) => {
        try {
          // set the filter and perform update
          self.filters[field] = value;
          if (self.table === 'profiles') {
            const id = self.filters.id;
            if (!id) throw new Error('Missing id for profile update');
            await profileApi.updateProfile(id, updates as any);
            return { data: updates, error: null };
          }
          return { data: updates, error: null };
        } catch (error) {
          return { data: null, error };
        }
      },
    };
  }

  delete() {
    // Make delete chainable so callers can do .delete().eq(...).eq(...)
    (this as any)._operation = 'delete';
    return this;
  }

  // Make the QueryBuilder thenable so callers can await the chain: e.g.
  // await supabase.from('likes').delete().eq('user_id', user.id).eq('video_id', vid)
  then(onfulfilled?: any, onrejected?: any): Promise<any> {
    const exec = async () => {
      try {
        // Handle delete operation if set
        if ((this as any)._operation === 'delete') {
          if (this.table === 'likes' && this.filters.user_id && this.filters.video_id) {
            await socialApi.unlikeVideo(this.filters.user_id, this.filters.video_id);
            return { data: { removed: 1 }, error: null };
          }
          if (this.table === 'follows' && this.filters.follower_id && this.filters.following_id) {
            await socialApi.unfollowUser(this.filters.follower_id, this.filters.following_id);
            return { data: { removed: 1 }, error: null };
          }
          if (this.table === 'comments' && this.filters.id) {
            await socialApi.deleteComment(this.filters.id);
            return { data: { removed: 1 }, error: null };
          }
          return { data: { removed: 0 }, error: null };
        }

        // Profiles
        if (this.table === 'profiles') {
          if (this.filters.id) {
            const data = await profileApi.getProfile(this.filters.id);
            return { data, error: null };
          }
          return { data: null, error: null };
        }

        // Videos
        if (this.table === 'videos') {
          if (this.filters.id) {
            const data = await videoApi.getVideo(this.filters.id);
            return { data, error: null };
          }

          const limit = this._limit ?? 50;
          const offset = this._offset ?? 0;

          if (this.filters.owner_id || this.filters.user_id) {
            const owner = this.filters.owner_id || this.filters.user_id;
            const data = await profileApi.getUserVideos(owner, limit, offset);
            const count = Array.isArray(data) ? data.length : 0;
            return { data, count, error: null };
          }

          // Basic listing/search fallback
          const data = await videoApi.listVideos(limit, offset);
          const count = Array.isArray(data) ? data.length : 0;
          // Respect select count option
          if (this._selectOptions && this._selectOptions.count === 'exact') {
            return { data, count, error: null };
          }
          return { data, error: null };
        }

        // Likes
        if (this.table === 'likes') {
          if (this.filters.user_id && this.filters.video_id) {
            const liked = await socialApi.checkLike(this.filters.user_id, this.filters.video_id);
            return { data: liked ? [{ id: 1 }] : [], count: liked ? 1 : 0, error: null };
          }
          return { data: [], count: 0, error: null };
        }

        // Follows
        if (this.table === 'follows') {
          if (this.filters.follower_id && this.filters.following_id) {
            const following = await socialApi.checkFollow(this.filters.follower_id, this.filters.following_id);
            return { data: following ? [{ id: 1 }] : [], count: following ? 1 : 0, error: null };
          }
          return { data: [], count: 0, error: null };
        }

        // Comments
        if (this.table === 'comments') {
          if (this.filters.video_id) {
            const comments = await socialApi.getComments(this.filters.video_id.toString());
            return { data: comments, count: Array.isArray(comments) ? comments.length : 0, error: null };
          }
          return { data: [], count: 0, error: null };
        }

        // Default
        return { data: null, error: null };
      } catch (err) {
        return Promise.reject(err);
      }
    };

    return exec().then(onfulfilled, onrejected);
  }
}

const storage = {
  from: (_bucket: string) => ({
    upload: async (_path: string, _file: File | Blob) => {
      // File uploads are handled by the upload API
      return { error: null };
    },
    getPublicUrl: (path: string) => {
      return { data: { publicUrl: path } };
    },
  }),
  createBucket: async (_name: string, _opts?: any) => {
    // No-op for now; backend storage is handled by upload API
    return { error: null };
  },
};

const auth = {
  getSession: async () => {
    const token = localStorage.getItem('clipstream_token');
    const userId = localStorage.getItem('clipstream_user_id');
    if (token && userId) {
      return { data: { session: { user: { id: userId } } } };
    }
    return { data: { session: null } };
  },
  onAuthStateChange: (_cb: (event: string, session: any) => void) => {
    const subscription = { unsubscribe: () => {} };
    return { data: { subscription } };
  },
  signUp: async ({ email, password }: { email: string; password: string }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data: any = await handleResponse(response);
      return { data: { user: { id: data.user_id, email } }, error: null };
    } catch (error) {
      return { data: null, error };
    }
  },
  signInWithPassword: async ({ email, password }: { email: string; password: string }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data: any = await handleResponse(response);
      localStorage.setItem('clipstream_token', data.access_token);
      localStorage.setItem('clipstream_user_id', data.user_id);
      return { data: { user: { id: data.user_id, email } }, error: null };
    } catch (error) {
      return { data: null, error };
    }
  },
  signOut: async () => {
    try {
      // Attempt to clear server-side session (cookies) for OAuth flows
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      // ignore network errors; proceed to clear client state
      console.warn('Failed to call backend logout:', err);
    }

    // Clear client-side stored tokens and remember flag
    try {
      localStorage.removeItem('clipstream_token');
      localStorage.removeItem('clipstream_user_id');
      localStorage.removeItem('clipstream_remember');
      localStorage.removeItem('access_token');
      sessionStorage.clear();
    } catch (e) {
      // ignore storage errors
    }

    return { error: null };
  },
};

const surreal: any = {
  from: (table: string) => new QueryBuilder(table),
  storage,
  auth,
  rpc: async (_name: string, _params?: any) => {
    // Map known rpc names to backend APIs where possible
    try {
      // Example: monetization rpc names could be implemented here
      // No-op default: return null data
      return { data: null, error: null };
    } catch (err) {
      return { data: null, error: err };
    }
  },
};

export { surreal };
