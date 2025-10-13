import { useState, useEffect } from 'react';
import { User, Video, Heart, Calendar, Settings } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { EditProfileModal } from './EditProfileModal';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Database } from '../../lib/database.types';

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
  const { user: currentUser, profile: currentProfile } = useAuth();
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

  const targetUserId = userId || currentUser?.id;
  const isOwnProfile = currentUser?.id === targetUserId;

  useEffect(() => {
    if (targetUserId) {
      loadProfile();
      loadVideos();
      loadStats();
      if (!isOwnProfile) {
        checkFollowStatus();
      }
    }
  }, [targetUserId]);

  const loadProfile = async () => {
    if (!targetUserId) return;

    const { data } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', targetUserId)
      .maybeSingle();

    if (data) {
      setProfile(data);
    }
  };

  const loadVideos = async () => {
    if (!targetUserId) return;

    const { data } = await supabase
      .from('videos')
      .select('*')
      .eq('user_id', targetUserId)
      .order('created_at', { ascending: false });

    if (data) {
      setVideos(data);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    if (!targetUserId) return;

    const [videosResult, likesResult, followersResult, followingResult] = await Promise.all([
      supabase.from('videos').select('id', { count: 'exact' }).eq('user_id', targetUserId),
      supabase.from('videos').select('likes_count').eq('user_id', targetUserId),
      supabase.from('follows').select('id', { count: 'exact' }).eq('following_id', targetUserId),
      supabase.from('follows').select('id', { count: 'exact' }).eq('follower_id', targetUserId),
    ]);

    const totalLikes = likesResult.data?.reduce((sum, video) => sum + video.likes_count, 0) || 0;

    setStats({
      videosCount: videosResult.count || 0,
      likesCount: totalLikes,
      followersCount: followersResult.count || 0,
      followingCount: followingResult.count || 0,
    });
  };

  const checkFollowStatus = async () => {
    if (!currentUser || !targetUserId) return;

    const { data } = await supabase
      .from('follows')
      .select('id')
      .eq('follower_id', currentUser.id)
      .eq('following_id', targetUserId)
      .maybeSingle();

    setIsFollowing(!!data);
  };

  const toggleFollow = async () => {
    if (!currentUser || !targetUserId) return;

    if (isFollowing) {
      await supabase
        .from('follows')
        .delete()
        .eq('follower_id', currentUser.id)
        .eq('following_id', targetUserId);

      setIsFollowing(false);
      setStats(prev => ({ ...prev, followersCount: prev.followersCount - 1 }));
    } else {
      await supabase
        .from('follows')
        .insert({ follower_id: currentUser.id, following_id: targetUserId });

      setIsFollowing(true);
      setStats(prev => ({ ...prev, followersCount: prev.followersCount + 1 }));
    }
  };

  if (loading || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">Loading profile...</div>
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
