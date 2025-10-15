import { useState, useEffect } from 'react';
import { Heart, MessageCircle, Share2, User, QrCode } from 'lucide-react';
import { surreal } from '../../lib/surrealdb';
import { useAuth } from '../../contexts/AuthContext';
import { QRCodeShare } from '../Share/QRCodeShare';
import type { Database } from '../../lib/database.types';

type Video = Database['public']['Tables']['videos']['Row'] & {
  profiles: Database['public']['Tables']['profiles']['Row'];
};

interface VideoCardProps {
  video: Video;
  onCommentClick: () => void;
}

export function VideoCard({ video, onCommentClick }: VideoCardProps) {
  const { user } = useAuth();
  const [isLiked, setIsLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(video.likes_count);
  const [isFollowing, setIsFollowing] = useState(false);
  const [showQRCode, setShowQRCode] = useState(false);

  useEffect(() => {
    if (user) {
      checkLikeStatus();
      checkFollowStatus();
    }
  }, [user, video.id]);

  const checkLikeStatus = async () => {
    if (!user) return;

    const { data } = await supabase
      .from('likes')
      .select('id')
      .eq('user_id', user.id)
      .eq('video_id', video.id)
      .maybeSingle();

    setIsLiked(!!data);
  };

  const checkFollowStatus = async () => {
    if (!user || user.id === video.user_id) return;

    const { data } = await supabase
      .from('follows')
      .select('id')
      .eq('follower_id', user.id)
      .eq('following_id', video.user_id)
      .maybeSingle();

    setIsFollowing(!!data);
  };

  const toggleLike = async () => {
    if (!user) return;

    if (isLiked) {
      await supabase
        .from('likes')
        .delete()
        .eq('user_id', user.id)
        .eq('video_id', video.id);

      setIsLiked(false);
      setLikesCount(prev => prev - 1);
    } else {
      await supabase
        .from('likes')
        .insert({ user_id: user.id, video_id: video.id });

      setIsLiked(true);
      setLikesCount(prev => prev + 1);
    }
  };

  const toggleFollow = async () => {
    if (!user || user.id === video.user_id) return;

    if (isFollowing) {
      await supabase
        .from('follows')
        .delete()
        .eq('follower_id', user.id)
        .eq('following_id', video.user_id);

      setIsFollowing(false);
    } else {
      await supabase
        .from('follows')
        .insert({ follower_id: user.id, following_id: video.user_id });

      setIsFollowing(true);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: video.title,
        text: video.description,
        url: window.location.href,
      });
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden max-w-lg w-full">
      <div className="aspect-[9/16] bg-black relative">
        <video
          src={video.video_url}
          className="w-full h-full object-contain"
          controls
          playsInline
        />
      </div>

      <div className="p-4 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              {video.profiles.avatar_url ? (
                <img
                  src={video.profiles.avatar_url}
                  alt={video.profiles.display_name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <User className="w-6 h-6 text-white" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">
                {video.profiles.display_name}
              </h3>
              <p className="text-sm text-gray-500">@{video.profiles.username}</p>
            </div>
          </div>

          {user && user.id !== video.user_id && (
            <button
              onClick={toggleFollow}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                isFollowing
                  ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isFollowing ? 'Following' : 'Follow'}
            </button>
          )}
        </div>

        <div>
          <h2 className="font-semibold text-lg text-gray-900 mb-1">{video.title}</h2>
          {video.description && (
            <p className="text-gray-600 text-sm">{video.description}</p>
          )}
        </div>

        <div className="flex items-center gap-6 pt-2 border-t border-gray-100">
          <button
            onClick={toggleLike}
            className="flex items-center gap-2 hover:text-red-600 transition group"
          >
            <Heart
              className={`w-6 h-6 ${
                isLiked ? 'fill-red-600 text-red-600' : 'text-gray-700 group-hover:text-red-600'
              }`}
            />
            <span className="font-semibold text-gray-900">{likesCount}</span>
          </button>

          <button
            onClick={onCommentClick}
            className="flex items-center gap-2 hover:text-blue-600 transition group"
          >
            <MessageCircle className="w-6 h-6 text-gray-700 group-hover:text-blue-600" />
            <span className="font-semibold text-gray-900">{video.comments_count}</span>
          </button>

          <button
            onClick={handleShare}
            className="flex items-center gap-2 hover:text-green-600 transition group"
          >
            <Share2 className="w-6 h-6 text-gray-700 group-hover:text-green-600" />
            <span className="font-semibold text-gray-900">{video.shares_count}</span>
          </button>

          <button
            onClick={() => setShowQRCode(true)}
            className="flex items-center gap-2 hover:text-cyber-purple transition group"
          >
            <QrCode className="w-6 h-6 text-gray-700 group-hover:text-cyber-purple" />
          </button>
        </div>
      </div>

      {showQRCode && (
        <QRCodeShare
          videoId={video.id}
          videoTitle={video.title}
          onClose={() => setShowQRCode(false)}
        />
      )}
    </div>
  );
}
