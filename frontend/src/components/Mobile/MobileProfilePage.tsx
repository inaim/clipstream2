import { useState, useEffect } from 'react';
import { User, Settings, Share2, MoreHorizontal, Grid2x2 as Grid, Heart } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { EditProfileModal } from '../Profile/EditProfileModal';
import type { Database } from '../../lib/database.types';

type Profile = Database['public']['Tables']['profiles']['Row'];
type VideoType = Database['public']['Tables']['videos']['Row'];

export function MobileProfilePage() {
  const { user, profile: currentProfile, signOut } = useAuth();
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [likedVideos, setLikedVideos] = useState<VideoType[]>([]);
  const [activeTab, setActiveTab] = useState<'videos' | 'liked'>('videos');
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    if (user) {
      loadVideos();
      loadLikedVideos();
    }
  }, [user]);

  const loadVideos = async () => {
    if (!user) return;

    const { data } = await supabase
      .from('videos')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (data) {
      setVideos(data);
    }
    setLoading(false);
  };

  const loadLikedVideos = async () => {
    if (!user) return;

    const { data: likes } = await supabase
      .from('likes')
      .select('video_id')
      .eq('user_id', user.id);

    if (likes && likes.length > 0) {
      const videoIds = likes.map(l => l.video_id);
      const { data } = await supabase
        .from('videos')
        .select('*')
        .in('id', videoIds)
        .order('created_at', { ascending: false });

      if (data) {
        setLikedVideos(data);
      }
    }
  };

  if (!currentProfile) {
    return (
      <div className="h-full flex items-center justify-center bg-black">
        <div className="text-white">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="h-full bg-black text-white overflow-y-auto pb-20">
      <div className="sticky top-0 bg-black/95 backdrop-blur-sm z-10 px-4 py-3 flex items-center justify-between border-b border-gray-800">
        <button
          onClick={() => alert('More options coming soon!')}
          className="p-2 hover:bg-gray-800 rounded-full transition active:scale-95"
        >
          <MoreHorizontal className="w-6 h-6" />
        </button>
        <span className="font-semibold text-lg">@{currentProfile.username}</span>
        <button
          onClick={signOut}
          className="p-2 hover:bg-gray-800 rounded-full transition active:scale-95"
        >
          <Settings className="w-6 h-6" />
        </button>
      </div>

      <div className="px-4 py-6">
        <div className="flex flex-col items-center mb-6">
          <div className="w-24 h-24 rounded-full bg-gradient-cyber flex items-center justify-center mb-4">
            {currentProfile.avatar_url ? (
              <img
                src={currentProfile.avatar_url}
                alt={currentProfile.display_name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <User className="w-12 h-12 text-white" />
            )}
          </div>

          <h1 className="text-2xl font-bold mb-1">{currentProfile.display_name}</h1>
          <p className="text-gray-400">@{currentProfile.username}</p>
        </div>

        <div className="flex justify-center gap-8 mb-6">
          <div className="text-center">
            <div className="text-xl font-bold">{currentProfile.following_count || 0}</div>
            <div className="text-xs text-gray-400">Following</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold">{currentProfile.followers_count || 0}</div>
            <div className="text-xs text-gray-400">Followers</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold">
              {videos.reduce((sum, v) => sum + v.likes_count, 0)}
            </div>
            <div className="text-xs text-gray-400">Likes</div>
          </div>
        </div>

        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setShowEditModal(true)}
            className="flex-1 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg font-semibold hover:opacity-90 transition active:scale-95"
          >
            Edit profile
          </button>
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: currentProfile.display_name,
                  text: `Check out @${currentProfile.username} on ClipStream!`,
                  url: window.location.href,
                });
              } else {
                navigator.clipboard.writeText(window.location.href);
                alert('Profile link copied to clipboard!');
              }
            }}
            className="flex-1 py-2 bg-gray-800 rounded-lg font-semibold hover:bg-gray-700 transition active:scale-95"
          >
            Share profile
          </button>
        </div>

        {currentProfile.bio && (
          <p className="text-center text-gray-300 mb-6">{currentProfile.bio}</p>
        )}

        <div className="border-t border-gray-800 flex">
          <button
            onClick={() => setActiveTab('videos')}
            className={`flex-1 py-4 flex items-center justify-center gap-2 border-b-2 transition ${
              activeTab === 'videos'
                ? 'border-white text-white'
                : 'border-transparent text-gray-400'
            }`}
          >
            <Grid className="w-5 h-5" />
            Videos
          </button>
          <button
            onClick={() => setActiveTab('liked')}
            className={`flex-1 py-4 flex items-center justify-center gap-2 border-b-2 transition ${
              activeTab === 'liked'
                ? 'border-white text-white'
                : 'border-transparent text-gray-400'
            }`}
          >
            <Heart className="w-5 h-5" />
            Liked
          </button>
        </div>

        <div className="grid grid-cols-3 gap-1 mt-1">
          {(activeTab === 'videos' ? videos : likedVideos).map((video) => (
            <div
              key={video.id}
              className="aspect-[9/16] bg-gray-900 relative group"
            >
              <video
                src={video.video_url}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-2 left-2 flex items-center gap-1">
                <Heart className="w-4 h-4" />
                <span className="text-xs font-semibold">{video.likes_count}</span>
              </div>
            </div>
          ))}
        </div>

        {(activeTab === 'videos' ? videos : likedVideos).length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-500">
              {activeTab === 'videos' ? 'No videos yet' : 'No liked videos yet'}
            </p>
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
