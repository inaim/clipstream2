/**
 * ClipStream API Service
 * Handles all backend API calls for the frontend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

/**
 * Get authorization header from localStorage
 */
function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

/**
 * Upload a video file to the backend
 */
export async function uploadViaBackend(
  file: File,
  title?: string
): Promise<{ video_id: string; playback_url: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title || 'Untitled');

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Failed to upload video');
  }

  return response.json();
}

/**
 * Get playback URL for a video
 */
export async function getPlaybackUrl(videoId: string): Promise<{ playback_url: string }> {
  const response = await fetch(`${API_BASE_URL}/api/playback/${videoId}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    throw new Error('Failed to get playback URL');
  }

  return response.json();
}

/**
 * Authentication API
 */
export const authApi = {
  /**
   * Register a new user
   */
  async register(email: string, password: string, displayName?: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Failed to register');
    }

    return response.json();
  },

  /**
   * Login with email and password
   */
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Invalid credentials');
    }

    return response.json();
  },

  /**
   * Get current user profile
   */
  async getProfile(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}`, {
      headers: getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to get user profile');
    }

    return response.json();
  },
};

/**
 * Feed API
 */
export const feedApi = {
  /**
   * Get For You feed
   */
  async getForYouFeed(userId?: string, limit = 20, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (userId) {
      params.append('user_id', userId);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/feed/for-you?${params}`, {
      headers: getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to load feed');
    }

    return response.json();
  },

  /**
   * Get Following feed
   */
  async getFollowingFeed(userId: string, limit = 20, offset = 0) {
    const params = new URLSearchParams({
      user_id: userId,
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/api/v1/feed/following?${params}`, {
      headers: getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to load following feed');
    }

    return response.json();
  },
};

/**
 * Video API
 */
export const videoApi = {
  /**
   * Get video details
   */
  async getVideo(videoId: string) {
    const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
      headers: getAuthHeader(),
    });

    if (!response.ok) {
      throw new Error('Failed to get video');
    }

    return response.json();
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

    if (!response.ok) {
      throw new Error('Failed to list videos');
    }

    return response.json();
  },

  /**
   * Record a view
   */
  async recordView(videoId: string, duration: number) {
    const response = await fetch(`${API_BASE_URL}/api/views`, {
      method: 'POST',
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ video_id: videoId, duration }),
    });

    if (!response.ok) {
      throw new Error('Failed to record view');
    }

    return response.json();
  },
};

/**
 * Social API
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
      body: JSON.stringify({ user_id: userId, video_id: videoId }),
    });

    if (!response.ok) {
      throw new Error('Failed to like video');
    }

    return response.json();
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
      body: JSON.stringify({ user_id: userId, video_id: videoId }),
    });

    if (!response.ok) {
      throw new Error('Failed to unlike video');
    }

    return response.json();
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
      body: JSON.stringify({ follower_id: followerId, following_id: followingId }),
    });

    if (!response.ok) {
      throw new Error('Failed to follow user');
    }

    return response.json();
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
      body: JSON.stringify({ follower_id: followerId, following_id: followingId }),
    });

    if (!response.ok) {
      throw new Error('Failed to unfollow user');
    }

    return response.json();
  },
};

// Export default object with all APIs
export default {
  uploadViaBackend,
  getPlaybackUrl,
  auth: authApi,
  feed: feedApi,
  video: videoApi,
  social: socialApi,
};

