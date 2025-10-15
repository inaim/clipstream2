/**
 * SurrealDB Backend Service
 * Replaces all Supabase calls with SurrealDB backend API calls
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     import.meta.env.VITE_BACKEND_URL || 
                     'http://localhost:8080';

/**
 * Get authorization header from localStorage
 */
function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('clipstream_token') || localStorage.getItem('access_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * Profile/User API
 */
export const profileApi = {
  /**
   * Get user profile by ID
   */
  async getProfile(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },

  /**
   * Update user profile
   */
  async updateProfile(userId: string, updates: { display_name?: string; bio?: string; avatar_url?: string }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
      method: 'PATCH',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    return handleResponse(response);
  },

  /**
   * Get user's videos
   */
  async getUserVideos(userId: string, limit = 50, offset = 0) {
    const params = new URLSearchParams({
      owner_id: userId,
      limit: limit.toString(),
      offset: offset.toString(),
    });
    const response = await fetch(`${API_BASE_URL}/api/videos?${params}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },

  /**
   * Get user stats (followers, following, likes)
   */
  async getUserStats(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/stats`, {
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },
};

/**
 * Video API
 */
export const videoApi = {
  /**
   * Get video by ID
   */
  async getVideo(videoId: string) {
    const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },

  /**
   * List videos
   */
  async listVideos(limit = 50, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    const response = await fetch(`${API_BASE_URL}/api/videos?${params}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },

  /**
   * Record a view
   */
  async recordView(videoId: string, duration: number, userId?: string) {
    const response = await fetch(`${API_BASE_URL}/api/views`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        video_id: parseInt(videoId.replace('video:', '')), 
        duration,
        user_id: userId ? parseInt(userId.replace('user:', '')) : undefined
      }),
    });
    return handleResponse(response);
  },
};

/**
 * Social API (Likes, Follows, Comments)
 */
export const socialApi = {
  /**
   * Like a video
   */
  async likeVideo(userId: string, videoId: string) {
    const response = await fetch(`${API_BASE_URL}/api/likes`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: parseInt(userId.replace('user:', '')), 
        video_id: parseInt(videoId.replace('video:', ''))
      }),
    });
    return handleResponse(response);
  },

  /**
   * Unlike a video
   */
  async unlikeVideo(userId: string, videoId: string) {
    const response = await fetch(`${API_BASE_URL}/api/likes`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: parseInt(userId.replace('user:', '')), 
        video_id: parseInt(videoId.replace('video:', ''))
      }),
    });
    return handleResponse(response);
  },

  /**
   * Check if user liked a video
   */
  async checkLike(userId: string, videoId: string) {
    const params = new URLSearchParams({
      user_id: userId.replace('user:', ''),
      video_id: videoId.replace('video:', ''),
    });
    const response = await fetch(`${API_BASE_URL}/api/likes?${params}`, {
      headers: getAuthHeader(),
    });
    const data = await handleResponse<{ data: any }>(response);
    return !!data.data;
  },

  /**
   * Follow a user
   */
  async followUser(followerId: string, followingId: string) {
    const response = await fetch(`${API_BASE_URL}/api/follows`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        follower_id: parseInt(followerId.replace('user:', '')), 
        following_id: parseInt(followingId.replace('user:', ''))
      }),
    });
    return handleResponse(response);
  },

  /**
   * Unfollow a user
   */
  async unfollowUser(followerId: string, followingId: string) {
    const response = await fetch(`${API_BASE_URL}/api/follows`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        follower_id: parseInt(followerId.replace('user:', '')), 
        following_id: parseInt(followingId.replace('user:', ''))
      }),
    });
    return handleResponse(response);
  },

  /**
   * Check if user is following another user
   */
  async checkFollow(followerId: string, followingId: string) {
    const params = new URLSearchParams({
      follower_id: followerId.replace('user:', ''),
      following_id: followingId.replace('user:', ''),
    });
    const response = await fetch(`${API_BASE_URL}/api/follows?${params}`, {
      headers: getAuthHeader(),
    });
    const data = await handleResponse<{ data: any }>(response);
    return !!data.data;
  },

  /**
   * Get comments for a video
   */
  async getComments(videoId: string) {
    const params = new URLSearchParams({
      video_id: videoId.replace('video:', ''),
    });
    const response = await fetch(`${API_BASE_URL}/api/comments?${params}`, {
      headers: getAuthHeader(),
    });
    return handleResponse<any[]>(response);
  },

  /**
   * Post a comment
   */
  async postComment(videoId: string, userId: string, content: string, parentId?: string) {
    const response = await fetch(`${API_BASE_URL}/api/comments`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        video_id: parseInt(videoId.replace('video:', '')),
        user_id: parseInt(userId.replace('user:', '')),
        content,
        parent_id: parentId ? parseInt(parentId) : null
      }),
    });
    return handleResponse(response);
  },
  
  /**
   * Delete a comment by id
   */
  async deleteComment(commentId: string) {
    const response = await fetch(`${API_BASE_URL}/api/comments/${commentId}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    return handleResponse(response);
  },
};

/**
 * Monetization API (Gifts, Ledger)
 */
export const monetizationApi = {
  /**
   * Send a gift
   */
  async sendGift(fromUserId: string, toUserId: string, amount: number) {
    const response = await fetch(`${API_BASE_URL}/api/gifts`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        from_user: parseInt(fromUserId.replace('user:', '')),
        to_user: parseInt(toUserId.replace('user:', '')),
        amount
      }),
    });
    return handleResponse(response);
  },

  /**
   * Get user's ledger (transaction history)
   */
  async getLedger(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/ledger/${userId.replace('user:', '')}`, {
      headers: getAuthHeader(),
    });
    return handleResponse<any[]>(response);
  },

  /**
   * Get user's balance
   */
  async getBalance(userId: string) {
    const ledger = await this.getLedger(userId);
    const balance = ledger.reduce((sum, entry) => sum + (entry.amount || 0), 0);
    return balance;
  },
};

/**
 * Export a Supabase-compatible interface for easy migration
 */
export const db = {
  profiles: profileApi,
  videos: videoApi,
  social: socialApi,
  monetization: monetizationApi,
};

export default db;

