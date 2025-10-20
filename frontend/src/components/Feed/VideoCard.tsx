import { useState, useEffect, useRef } from 'react';
import { User } from 'lucide-react';
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
  isPlaying?: boolean;
  onPlay?: () => void;
  onPause?: () => void;
}

export function VideoCard({ video, onCommentClick, isPlaying, onPlay, onPause }: VideoCardProps) {
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

    const { data } = await surreal
      .from('likes')
      .select('id')
      .eq('user_id', user.id)
      .eq('video_id', video.id)
      .maybeSingle();

    setIsLiked(!!data);
  };

  const checkFollowStatus = async () => {
    if (!user || user.id === video.user_id) return;

    const { data } = await surreal
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
      await surreal
        .from('likes')
        .delete()
        .eq('user_id', user.id)
        .eq('video_id', video.id);

      setIsLiked(false);
      setLikesCount(prev => prev - 1);
    } else {
      await surreal
        .from('likes')
        .insert({ user_id: user.id, video_id: video.id });

      setIsLiked(true);
      setLikesCount(prev => prev + 1);
    }
  };

  const toggleFollow = async () => {
    if (!user || user.id === video.user_id) return;

    if (isFollowing) {
      await surreal
        .from('follows')
        .delete()
        .eq('follower_id', user.id)
        .eq('following_id', video.user_id);

      setIsFollowing(false);
    } else {
      await surreal
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

  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (isPlaying) {
      videoRef.current?.play();
    } else {
      videoRef.current?.pause();
    }
  }, [isPlaying]);

  const handlePlayPause = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying) {
      onPause && onPause();
    } else {
      onPlay && onPlay();
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden w-full max-w-[420px] md:max-w-[520px] lg:max-w-[600px] mx-auto">
      <div className="aspect-[9/16] bg-black relative group cursor-pointer" onClick={onCommentClick} tabIndex={0} role="button" aria-label="Open comments/discussion">
        {/* status badge */}
        {((video as any).status || (video as any).processing_steps) && (
          <div className="absolute top-3 left-3 z-10">
            <span className={`px-2 py-1 text-xs font-semibold rounded-full text-white ${((video as any).status === 'queued' && 'bg-yellow-600') || ((video as any).status === 'processing' && 'bg-orange-600') || ((video as any).status === 'failed' && 'bg-red-600') || 'bg-green-600'}`}>
              {((video as any).status && ((video as any).status).toString().toUpperCase()) || 'PROCESSING'}
            </span>
          </div>
        )}
        <video
          ref={videoRef}
          src={video.video_url}
          className="w-full h-full object-contain pointer-events-none group-focus:outline-none"
          controls={false}
          playsInline
        />
        {/* Play/Pause overlay button */}
        <button
          className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 text-white rounded-full px-4 py-2 text-lg z-20 hover:bg-black/80 focus:outline-none"
          onClick={handlePlayPause}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        {/* processing overlay for queued/processing videos */}
        {((video as any).status === 'queued' || (video as any).status === 'processing') && (video as any).processing_steps && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-20">
            <div className="bg-white/90 rounded-lg p-4 max-w-sm w-full text-center">
              <h4 className="font-semibold mb-2">Processing</h4>
              <div className="text-sm text-gray-700">
                {Object.entries((video as any).processing_steps).map(([k, v]: any) => (
                  <div key={k} className="flex justify-between py-1">
                    <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-xs text-gray-600">{v?.status || ''}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

  <div className="p-3 sm:p-4 space-y-4">
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

        <div className="flex items-center justify-between gap-4 pt-2 border-t border-gray-100 text-2xl">
          <button
            onClick={toggleLike}
            className="hover:text-red-600 transition"
            title="Like"
          >
            {isLiked ? '❤️' : '🤍'} <span className="text-base align-middle ml-1">{likesCount}</span>
          </button>
          <button
            onClick={onCommentClick}
            className="hover:text-blue-600 transition"
            title="Comment"
          >
            💬 <span className="text-base align-middle ml-1">{video.comments_count}</span>
          </button>
          <button
            onClick={handleShare}
            className="hover:text-green-600 transition"
            title="Share"
          >
            📤 <span className="text-base align-middle ml-1">{video.shares_count}</span>
          </button>
          <button
            onClick={() => setShowQRCode(true)}
            className="hover:text-purple-600 transition"
            title="QR Code"
          >
            🧩
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
