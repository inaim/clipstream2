# 📱 Frontend & Mobile API Integration Guide

Complete guide for using SurrealDB backend APIs in frontend and mobile components.

---

## 🎯 Quick Start

### Import the Services

```typescript
// Option 1: Use Supabase-compatible interface (recommended for existing code)
import { supabase } from '../../lib/surrealdb';

// Option 2: Use direct API services (recommended for new code)
import { profileApi, videoApi, socialApi, monetizationApi } from '../../services/surrealdb';
```

---

## 🔐 Authentication

### Login

```typescript
import { supabase } from '../../lib/surrealdb';

// Using compatibility layer
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
});

if (data?.user) {
  console.log('Logged in:', data.user.id);
}
```

### Register

```typescript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
});
```

### Check Session

```typescript
const { data } = await supabase.auth.getSession();
if (data?.session) {
  console.log('User is logged in:', data.session.user.id);
}
```

### Logout

```typescript
await supabase.auth.signOut();
```

---

## 👤 Profile Operations

### Get User Profile

```typescript
import { profileApi } from '../../services/surrealdb';

// Direct API call
const profile = await profileApi.getProfile(userId);
console.log(profile.display_name, profile.bio);

// OR using Supabase interface
const { data } = await supabase
  .from('profiles')
  .select()
  .eq('id', userId)
  .maybeSingle();
```

### Update Profile

```typescript
await profileApi.updateProfile(userId, {
  display_name: 'New Name',
  bio: 'My awesome bio',
  avatar_url: 'https://example.com/avatar.jpg'
});
```

### Get User Stats

```typescript
const stats = await profileApi.getUserStats(userId);
console.log('Followers:', stats.followers_count);
console.log('Following:', stats.following_count);
console.log('Likes:', stats.total_likes);
```

### Get User's Videos

```typescript
const videos = await profileApi.getUserVideos(userId, 50, 0);
videos.forEach(video => {
  console.log(video.title, video.views_count);
});
```

---

## 🎥 Video Operations

### Get Video Details

```typescript
import { videoApi } from '../../services/surrealdb';

const video = await videoApi.getVideo(videoId);
console.log(video.title, video.video_url);
```

### List Videos (Feed)

```typescript
const videos = await videoApi.listVideos(50, 0);
// Returns array of videos with owner info, stats, etc.
```

### Record Video View

```typescript
// Record that user watched video for 30 seconds
await videoApi.recordView(videoId, 30, userId);
```

### Upload Video

```typescript
import { uploadViaBackend } from '../../services/api';

const file = document.querySelector('input[type="file"]').files[0];
const result = await uploadViaBackend(file, 'My Video Title');

console.log('Video ID:', result.video_id);
console.log('Playback URL:', result.playback_url);
```

---

## ❤️ Social Operations

### Like Video

```typescript
import { socialApi } from '../../services/surrealdb';

// Direct API
await socialApi.likeVideo(userId, videoId);

// OR Supabase interface
await supabase
  .from('likes')
  .insert({ user_id: userId, video_id: videoId });
```

### Unlike Video

```typescript
await socialApi.unlikeVideo(userId, videoId);

// OR
await supabase
  .from('likes')
  .delete()
  .eq('user_id', userId)
  .eq('video_id', videoId);
```

### Check if Liked

```typescript
const isLiked = await socialApi.checkLike(userId, videoId);
if (isLiked) {
  console.log('User has liked this video');
}
```

### Follow User

```typescript
await socialApi.followUser(myUserId, targetUserId);
```

### Unfollow User

```typescript
await socialApi.unfollowUser(myUserId, targetUserId);
```

### Check if Following

```typescript
const isFollowing = await socialApi.checkFollow(myUserId, targetUserId);
```

---

## 💬 Comments

### Get Comments

```typescript
const comments = await socialApi.getComments(videoId);
comments.forEach(comment => {
  console.log(comment.user_id, comment.content);
});
```

### Post Comment

```typescript
await socialApi.postComment(
  videoId,
  userId,
  'Great video!',
  null // parentId for replies
);
```

### Reply to Comment

```typescript
await socialApi.postComment(
  videoId,
  userId,
  'Thanks!',
  parentCommentId
);
```

---

## 💰 Monetization

### Send Gift

```typescript
import { monetizationApi } from '../../services/surrealdb';

await monetizationApi.sendGift(
  myUserId,
  creatorUserId,
  10.00 // amount
);
```

### Get Transaction History

```typescript
const transactions = await monetizationApi.getLedger(userId);
transactions.forEach(tx => {
  console.log(tx.reason, tx.amount, tx.created_at);
});
```

### Get Balance

```typescript
const balance = await monetizationApi.getBalance(userId);
console.log('Balance:', balance);
```

---

## 📱 Mobile-Specific Examples

### Mobile Profile Page

```typescript
import { useEffect, useState } from 'react';
import { profileApi, videoApi } from '../../services/surrealdb';

function MobileProfilePage({ userId }) {
  const [profile, setProfile] = useState(null);
  const [videos, setVideos] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadProfile();
  }, [userId]);

  async function loadProfile() {
    try {
      const [profileData, videosData, statsData] = await Promise.all([
        profileApi.getProfile(userId),
        profileApi.getUserVideos(userId, 20, 0),
        profileApi.getUserStats(userId)
      ]);
      
      setProfile(profileData);
      setVideos(videosData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  }

  return (
    <div>
      <h1>{profile?.display_name}</h1>
      <p>{profile?.bio}</p>
      <div>
        <span>{stats?.followers_count} Followers</span>
        <span>{stats?.following_count} Following</span>
      </div>
      {videos.map(video => (
        <VideoCard key={video.id} video={video} />
      ))}
    </div>
  );
}
```

### Mobile Video Feed

```typescript
import { useEffect, useState } from 'react';
import { videoApi, socialApi } from '../../services/surrealdb';

function MobileVideoFeed({ userId }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFeed();
  }, []);

  async function loadFeed() {
    try {
      const data = await videoApi.listVideos(20, 0);
      setVideos(data);
    } catch (error) {
      console.error('Failed to load feed:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleLike(videoId) {
    try {
      await socialApi.likeVideo(userId, videoId);
      // Update UI
      setVideos(videos.map(v => 
        v.id === videoId 
          ? { ...v, likes_count: v.likes_count + 1, is_liked: true }
          : v
      ));
    } catch (error) {
      console.error('Failed to like video:', error);
    }
  }

  return (
    <div>
      {videos.map(video => (
        <div key={video.id}>
          <video src={video.video_url} />
          <button onClick={() => handleLike(video.id)}>
            {video.is_liked ? '❤️' : '🤍'} {video.likes_count}
          </button>
        </div>
      ))}
    </div>
  );
}
```

### Mobile Comments Section

```typescript
import { useEffect, useState } from 'react';
import { socialApi } from '../../services/surrealdb';

function MobileComments({ videoId, userId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');

  useEffect(() => {
    loadComments();
  }, [videoId]);

  async function loadComments() {
    const data = await socialApi.getComments(videoId);
    setComments(data);
  }

  async function handlePostComment() {
    if (!newComment.trim()) return;
    
    try {
      await socialApi.postComment(videoId, userId, newComment, null);
      setNewComment('');
      await loadComments(); // Reload comments
    } catch (error) {
      console.error('Failed to post comment:', error);
    }
  }

  return (
    <div>
      <div>
        {comments.map(comment => (
          <div key={comment.id}>
            <strong>{comment.user_id}</strong>
            <p>{comment.content}</p>
          </div>
        ))}
      </div>
      <div>
        <input
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
        />
        <button onClick={handlePostComment}>Post</button>
      </div>
    </div>
  );
}
```

---

## 🔄 Real-time Updates (Future)

For real-time features, you can implement polling or WebSocket connections:

### Polling Example

```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const stats = await profileApi.getUserStats(userId);
    setStats(stats);
  }, 5000); // Update every 5 seconds

  return () => clearInterval(interval);
}, [userId]);
```

---

## 🎨 UI State Management

### Loading States

```typescript
const [loading, setLoading] = useState(false);

async function handleAction() {
  setLoading(true);
  try {
    await socialApi.likeVideo(userId, videoId);
  } catch (error) {
    console.error(error);
  } finally {
    setLoading(false);
  }
}
```

### Error Handling

```typescript
const [error, setError] = useState(null);

async function loadData() {
  try {
    setError(null);
    const data = await profileApi.getProfile(userId);
    setProfile(data);
  } catch (err) {
    setError(err.message);
  }
}

// In render
{error && <div className="error">{error}</div>}
```

---

## 🚀 Performance Tips

### 1. Batch Requests

```typescript
// Good: Load all data in parallel
const [profile, videos, stats] = await Promise.all([
  profileApi.getProfile(userId),
  profileApi.getUserVideos(userId),
  profileApi.getUserStats(userId)
]);

// Bad: Sequential requests
const profile = await profileApi.getProfile(userId);
const videos = await profileApi.getUserVideos(userId);
const stats = await profileApi.getUserStats(userId);
```

### 2. Cache Data

```typescript
const cache = new Map();

async function getCachedProfile(userId) {
  if (cache.has(userId)) {
    return cache.get(userId);
  }
  
  const profile = await profileApi.getProfile(userId);
  cache.set(userId, profile);
  return profile;
}
```

### 3. Debounce Actions

```typescript
import { debounce } from 'lodash';

const debouncedSearch = debounce(async (query) => {
  const results = await searchApi.search(query);
  setResults(results);
}, 300);
```

---

## 📚 Complete API Reference

| Service | Method | Description |
|---------|--------|-------------|
| **profileApi** | `getProfile(userId)` | Get user profile |
| | `updateProfile(userId, data)` | Update profile |
| | `getUserVideos(userId, limit, offset)` | Get user's videos |
| | `getUserStats(userId)` | Get follower/following counts |
| **videoApi** | `getVideo(videoId)` | Get video details |
| | `listVideos(limit, offset)` | List all videos |
| | `recordView(videoId, duration, userId)` | Record video view |
| **socialApi** | `likeVideo(userId, videoId)` | Like a video |
| | `unlikeVideo(userId, videoId)` | Unlike a video |
| | `checkLike(userId, videoId)` | Check if liked |
| | `followUser(followerId, followingId)` | Follow user |
| | `unfollowUser(followerId, followingId)` | Unfollow user |
| | `checkFollow(followerId, followingId)` | Check if following |
| | `getComments(videoId)` | Get video comments |
| | `postComment(videoId, userId, content, parentId)` | Post comment |
| **monetizationApi** | `sendGift(fromUserId, toUserId, amount)` | Send gift |
| | `getLedger(userId)` | Get transaction history |
| | `getBalance(userId)` | Get user balance |

---

## 🎉 Summary

All frontend and mobile components now use the SurrealDB backend through:

1. **Direct API calls** via `services/surrealdb.ts`
2. **Supabase-compatible interface** via `lib/surrealdb.ts`

Both approaches work seamlessly with the FastAPI backend and SurrealDB Cloud database.

**Your mobile and frontend services are fully integrated! 🚀**

