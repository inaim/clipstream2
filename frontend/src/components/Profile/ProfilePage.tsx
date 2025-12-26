import { useState, useEffect } from 'react';
import { User, Video, Heart, Calendar, Settings } from 'lucide-react';
import { authApi, videoApi, socialApi } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { EditProfileModal } from './EditProfileModal';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Database } from '../../lib/database.types';
import { useNavigate } from 'react-router-dom';

type Profile = Database['public']['Tables']['profiles']['Row'];
type VideoType = Database['public']['Tables']['videos']['Row'];

interface ProfileStats {
  videosCount: number;
  likesCount: number;
  followersCount: number;
  followingCount: number;
}

interface ProfilePageProps {
  userId?: string;
}

export function ProfilePage({ userId }: ProfilePageProps) {
  const { t } = useLanguage();
  const { user: currentUser, signOut } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [stats, setStats] = useState<ProfileStats>({
    videosCount: 0,
    likesCount: 0,
    followersCount: 0,
    followingCount: 0,
  });
  const [isFollowing, setIsFollowing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const navigate = useNavigate();

  const targetUserId = userId || currentUser?.id || (currentUser as any)?.user_id;
  const isOwnProfile = (currentUser?.id || (currentUser as any)?.user_id) === targetUserId;

  useEffect(() => {
    if (targetUserId) {
      loadProfile();
      loadVideos();
      loadStats();
      if (!isOwnProfile) {
        checkFollowStatus();
      }
    } else {
      setLoading(false);
    }
  }, [targetUserId]);

  const loadProfile = async () => {
    if (!targetUserId) return;
    try {
      const data = await authApi.getProfile(targetUserId);
      setProfile(data);
    } catch (err) {
      setProfile(null);
      setLoading(false);
    }
  };

  const loadVideos = async () => {
    if (!targetUserId) return;
    try {
      const allVideos = await videoApi.listVideos(50, 0);
      const userVideos = (allVideos || []).filter((v: any) => v.user_id === targetUserId);
      setVideos(userVideos);
    } catch (err) {
      setVideos([]);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    if (!targetUserId) return;
    try {
      const allVideos = await videoApi.listVideos(100, 0);
      const userVideos = (allVideos || []).filter((v: any) => v.user_id === targetUserId);
      const videosCount = userVideos.length;
      const likesCount = userVideos.reduce((sum: number, v: any) => sum + (v.likes_count || 0), 0);

      // Followers and following counts (best-effort; API may not exist in this build)
      let followersCount = 0;
      let followingCount = 0;
      const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
      try {
        const followersRes = await fetch(`${API_BASE}/api/follows?following_id=${targetUserId}`);
        if (followersRes.ok) {
          const followersData = await followersRes.json();
          followersCount = Array.isArray(followersData) ? followersData.length : 0;
        }
      } catch {
        // ignore missing endpoint
      }
      try {
        const followingRes = await fetch(`${API_BASE}/api/follows?follower_id=${targetUserId}`);
        if (followingRes.ok) {
          const followingData = await followingRes.json();
          followingCount = Array.isArray(followingData) ? followingData.length : 0;
        }
      } catch {
        // ignore missing endpoint
      }

      setStats({ videosCount, likesCount, followersCount, followingCount });
    } catch {
      setStats({ videosCount: 0, likesCount: 0, followersCount: 0, followingCount: 0 });
    }
  };

  const checkFollowStatus = async () => {
    if (!currentUser || !targetUserId) return;
    try {
      const followerId = String(currentUser.id || (currentUser as any)?.user_id || '');
      const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
      const res = await fetch(`${API_BASE}/api/follows?follower_id=${followerId}&following_id=${targetUserId}`);
      const data = await res.json();
      setIsFollowing(Array.isArray(data) && data.length > 0);
    } catch {
      setIsFollowing(false);
    }
  };

  const toggleFollow = async () => {
    if (!currentUser || !targetUserId) return;
    try {
      const followerId = String(currentUser.id);
      const followingId = String(targetUserId);
      if (isFollowing) {
        await socialApi.unfollowUser(followerId, followingId);
        setIsFollowing(false);
        setStats(prev => ({ ...prev, followersCount: prev.followersCount - 1 }));
      } else {
        await socialApi.followUser(followerId, followingId);
        setIsFollowing(true);
        setStats(prev => ({ ...prev, followersCount: prev.followersCount + 1 }));
      }
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-4">
          <div className="text-lg">Please sign in to view your profile.</div>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 rounded-lg bg-gray-200 text-gray-800 hover:bg-gray-300"
            >
              Go to landing
            </button>
            <button
              onClick={() => signOut()}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
        <div className="flex items-start gap-6 mb-8">
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt={profile.display_name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <User className="w-16 h-16 text-white" />
            )}
          </div>

          <div className="flex-1">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-1">
                  {profile.display_name}
                </h1>
                <p className="text-gray-500">@{profile.username}</p>
              </div>

              {isOwnProfile ? (
                <button
                  onClick={() => setShowEditModal(true)}
                  className="flex items-center gap-2 px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition"
                >
                  <Settings className="w-5 h-5" />
                  {t('profile.editProfile')}
                </button>
              ) : currentUser && (
                <button
                  onClick={toggleFollow}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    isFollowing
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {isFollowing ? t('profile.following') : t('profile.follow')}
                </button>
              )}
            </div>

            {profile.bio && (
              <p className="text-gray-700 mb-4">{profile.bio}</p>
            )}

            <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
              <Calendar className="w-4 h-4" />
              <span>Joined {new Date(profile.created_at).toLocaleDateString()}</span>
            </div>

            <div className="flex gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.videosCount}</div>
                <div className="text-sm text-gray-500">Videos</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.likesCount}</div>
                <div className="text-sm text-gray-500">Likes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.followersCount}</div>
                <div className="text-sm text-gray-500">Followers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.followingCount}</div>
                <div className="text-sm text-gray-500">Following</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <Video className="w-6 h-6" />
          Videos
        </h2>

        {videos.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
            <p className="text-gray-500 text-lg">No videos yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {videos.map((video) => (
              <div
                key={video.id}
                className="aspect-[9/16] bg-gray-900 rounded-lg overflow-hidden relative group cursor-pointer"
              >
                <video
                  src={video.video_url}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition text-white text-center">
                    <div className="flex items-center justify-center gap-4 mb-2">
                      <div className="flex items-center gap-1">
                        <Heart className="w-5 h-5" />
                        <span>{video.likes_count}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showEditModal && (
        <EditProfileModal
          onClose={() => setShowEditModal(false)}
          onSuccess={() => {
            window.location.reload();
          }}
        />
      )}
    </div>
  );
}
