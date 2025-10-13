import { useState, useEffect, useRef, useCallback } from 'react';
import { Heart, MessageCircle, Share2, Bookmark, Music, Search } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

type Video = {
  video_id: string;
  title: string;
  description: string;
  video_url: string;
  thumbnail_url: string;
  duration: number;
  user_id: string;
  username: string;
  display_name: string;
  avatar_url?: string;
  likes_count: number;
  comments_count: number;
  shares_count: number;
  created_at: string;
};

interface SwipeableVideoFeedProps {
  feedType: 'foryou' | 'following';
}

export function SwipeableVideoFeed({ feedType }: SwipeableVideoFeedProps) {
  const { user } = useAuth();
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [touchStart, setTouchStart] = useState(0);
  const [touchEnd, setTouchEnd] = useState(0);
  const [isLiked, setIsLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(0);
  const [showHeart, setShowHeart] = useState(false);

  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const lastTapRef = useRef(0);

  useEffect(() => {
    loadVideos();
  }, [feedType]);

  useEffect(() => {
    if (videos.length > 0) {
      checkLikeStatus();
      setLikesCount(videos[currentIndex]?.likes_count || 0);
      playCurrentVideo();
      trackView();
    }
  }, [currentIndex, videos]);

  const loadVideos = async () => {
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
      let endpoint = '/api/v1/feed/for-you';

      if (feedType === 'following') {
        endpoint = '/api/v1/feed/following';
      }

      const url = new URL(endpoint, API_BASE);
      if (user?.user_id) {
        url.searchParams.set('user_id', user.user_id);
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setVideos(data.items || []);
    } catch (error) {
      console.error('Error loading videos:', error);
      setVideos([]);
    }

    setLoading(false);
  };

  const playCurrentVideo = () => {
    videoRefs.current.forEach((video, index) => {
      if (video) {
        if (index === currentIndex) {
          video.play().catch(() => {});
        } else {
          video.pause();
          video.currentTime = 0;
        }
      }
    });
  };

  const trackView = async () => {
    if (!user || !videos[currentIndex]) return;

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
      await fetch(`${API_BASE}/api/v1/videos/${videos[currentIndex].video_id}/view`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('clipstream_token')}`
        },
        body: JSON.stringify({
          user_id: user.user_id,
          watch_duration: 0
        })
      });
    } catch (error) {
      console.error('Error tracking view:', error);
    }
  };

  const checkLikeStatus = async () => {
    if (!user || !videos[currentIndex]) return;

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
      const response = await fetch(`${API_BASE}/api/v1/videos/${videos[currentIndex].video_id}/like-status?user_id=${user.user_id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('clipstream_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setIsLiked(data.is_liked || false);
      }
    } catch (error) {
      console.error('Error checking like status:', error);
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientY);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const minSwipeDistance = 50;

    if (distance > minSwipeDistance && currentIndex < videos.length - 1) {
      setCurrentIndex(prev => prev + 1);
    }

    if (distance < -minSwipeDistance && currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }

    setTouchStart(0);
    setTouchEnd(0);
  };

  const handleDoubleTap = async () => {
    const now = Date.now();
    const timeSinceLastTap = now - lastTapRef.current;

    if (timeSinceLastTap < 300 && timeSinceLastTap > 0) {
      if (!isLiked) {
        await toggleLike();
        setShowHeart(true);
        setTimeout(() => setShowHeart(false), 1000);
      }
    }

    lastTapRef.current = now;
  };

  const toggleLike = async () => {
    if (!user || !videos[currentIndex]) return;

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
      const method = isLiked ? 'DELETE' : 'POST';
      const response = await fetch(`${API_BASE}/api/v1/videos/${videos[currentIndex].video_id}/like`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('clipstream_token')}`
        },
        body: JSON.stringify({
          user_id: user.user_id
        })
      });

      if (response.ok) {
        if (isLiked) {
          setIsLiked(false);
          setLikesCount(prev => prev - 1);
        } else {
          setIsLiked(true);
          setLikesCount(prev => prev + 1);
        }
      }
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const handleShare = async () => {
    const video = videos[currentIndex];
    if (navigator.share) {
      await navigator.share({
        title: video.title,
        text: video.description,
        url: window.location.href,
      });
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-black">
        <div className="text-white">Loading videos...</div>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-black">
        <div className="text-white text-center px-4">
          <p className="text-xl mb-2">No videos yet</p>
          <p className="text-gray-400">
            {feedType === 'following' ? 'Follow creators to see their videos' : 'Check back soon!'}
          </p>
        </div>
      </div>
    );
  }

  const currentVideo = videos[currentIndex];

  return (
    <div
      ref={containerRef}
      className="h-full relative bg-black overflow-hidden"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onClick={handleDoubleTap}
    >
      {videos.map((video, index) => (
        <div
          key={video.video_id}
          className={`absolute inset-0 transition-transform duration-300 ${
            index === currentIndex ? 'translate-y-0' : index < currentIndex ? '-translate-y-full' : 'translate-y-full'
          }`}
        >
          <video
            ref={el => videoRefs.current[index] = el}
            src={video.video_url}
            className="w-full h-full object-cover"
            loop
            playsInline
          />
        </div>
      ))}

      {showHeart && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-30">
          <Heart className="w-32 h-32 text-white fill-white animate-ping" />
        </div>
      )}

      <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/60 pointer-events-none" />

      <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between z-20">
        <div className="flex gap-6">
          <button
            className={`text-white font-semibold text-lg ${
              feedType === 'following' ? 'opacity-50' : ''
            }`}
          >
            For You
          </button>
          <button
            className={`text-white font-semibold text-lg ${
              feedType === 'foryou' ? 'opacity-50' : ''
            }`}
          >
            Following
          </button>
        </div>
        <button className="p-2">
          <Search className="w-6 h-6 text-white" />
        </button>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 pb-24 z-20">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-10 h-10 rounded-full bg-gradient-cyber border-2 border-white">
                {currentVideo.avatar_url && (
                  <img
                    src={currentVideo.avatar_url}
                    alt={currentVideo.username}
                    className="w-full h-full rounded-full object-cover"
                  />
                )}
              </div>
              <span className="text-white font-semibold">
                @{currentVideo.username}
              </span>
            </div>

            <h3 className="text-white font-semibold mb-2">{currentVideo.title}</h3>
            {currentVideo.description && (
              <p className="text-white text-sm mb-2">{currentVideo.description}</p>
            )}

            <div className="flex items-center gap-2 text-white text-sm">
              <Music className="w-4 h-4" />
              <span>Original sound - {currentVideo.display_name}</span>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <button onClick={toggleLike} className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mb-1">
                <Heart
                  className={`w-7 h-7 ${
                    isLiked ? 'fill-red-500 text-red-500' : 'text-white'
                  }`}
                />
              </div>
              <span className="text-white text-xs font-semibold">{likesCount}</span>
            </button>

            <button className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mb-1">
                <MessageCircle className="w-7 h-7 text-white" />
              </div>
              <span className="text-white text-xs font-semibold">
                {currentVideo.comments_count}
              </span>
            </button>

            <button className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mb-1">
                <Bookmark className="w-7 h-7 text-white" />
              </div>
              <span className="text-white text-xs font-semibold">Save</span>
            </button>

            <button onClick={handleShare} className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mb-1">
                <Share2 className="w-7 h-7 text-white" />
              </div>
              <span className="text-white text-xs font-semibold">
                {currentVideo.shares_count}
              </span>
            </button>
          </div>
        </div>
      </div>

      <div className="absolute right-4 top-1/2 -translate-y-1/2 z-20">
        <div className="flex flex-col gap-1">
          {videos.map((_, index) => (
            <div
              key={index}
              className={`w-1 h-1 rounded-full transition-all ${
                index === currentIndex ? 'bg-white h-3' : 'bg-white/50'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
