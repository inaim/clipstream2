const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleRes(res: Response) {
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!res.ok) throw new Error(data?.detail || data || res.statusText)
  return data
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('clipstream_token')
  const h: Record<string, string> = {}
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

export const surreal = {
  // Videos
  async createVideo(file: File, title: string) {
    const fd = new FormData();
    fd.append('file', file)
    fd.append('title', title)
    // Do NOT set Content-Type header for FormData; browser will add the correct boundary
    const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: fd, headers: authHeaders() })
    return handleRes(res)
  },

  async getVideo(videoId: string) {
    const res = await fetch(`${API_BASE}/api/videos/${videoId}`, { headers: authHeaders() })
    return handleRes(res)
  },

  async listVideos(limit = 50) {
    const res = await fetch(`${API_BASE}/api/videos?limit=${limit}`, { headers: authHeaders() })
    return handleRes(res)
  },

  // Users
  async getUser(userId: string) {
    const res = await fetch(`${API_BASE}/api/users/${userId}`, { headers: authHeaders() })
    return handleRes(res)
  },

  async updateUser(userId: string, payload: any) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/users/${userId}`, { method: 'PUT', headers, body: JSON.stringify(payload) })
    return handleRes(res)
  },

  // Likes
  async likeVideo(userId: string, videoId: string) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/likes`, { method: 'POST', headers, body: JSON.stringify({ user_id: userId, video_id: videoId }) })
    return handleRes(res)
  },

  async unlikeVideo(userId: string, videoId: string) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/likes`, { method: 'DELETE', headers, body: JSON.stringify({ user_id: userId, video_id: videoId }) })
    return handleRes(res)
  },

  // Follows
  async followUser(followerId: string, followingId: string) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/follows`, { method: 'POST', headers, body: JSON.stringify({ follower_id: followerId, following_id: followingId }) })
    return handleRes(res)
  },

  async unfollowUser(followerId: string, followingId: string) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/follows`, { method: 'DELETE', headers, body: JSON.stringify({ follower_id: followerId, following_id: followingId }) })
    return handleRes(res)
  },

  // Comments
  async createComment(payload: any) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders() }
    const res = await fetch(`${API_BASE}/api/comments`, { method: 'POST', headers, body: JSON.stringify(payload) })
    return handleRes(res)
  },

  async listComments(videoId: string) {
    const res = await fetch(`${API_BASE}/api/comments?video_id=${videoId}`, { headers: authHeaders() })
    return handleRes(res)
  }
}
