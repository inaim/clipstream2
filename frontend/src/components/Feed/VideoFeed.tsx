import { useState, useEffect } from 'react';
import type { Database } from '../../lib/database.types';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { VideoCard } from './VideoCard';
import { EnhancedCommentsModal } from './EnhancedCommentsModal';
import { Loader } from 'lucide-react';
// ...existing code...

type Video = Database['public']['Tables']['videos']['Row'] & {
  profiles: Database['public']['Tables']['profiles']['Row'];
};

export function VideoFeed() {
  const { t } = useLanguage();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    setLoading(true);
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 
           'http://localhost:8000';
    // For mock backend, fetch videos from API directly
    try {
      const res = await fetch(`${API_BASE}/api/v1/feed/for-you?user_id=` + (user?.user_id ?? 'user-a'));
      if (res.ok) {
        const json = await res.json();
        // map returned items to the Video type minimally
        const items = json.items.map((it: any) => ({
          id: it.video_id,
          video_url: it.cdn_url || '',
          title: it.title,
          likes_count: 0,
          comments_count: 0,
          shares_count: 0,
          user_id: '',
          profiles: { display_name: it.title, username: it.video_id, avatar_url: '' },
        }));
        setVideos(items as Video[]);
      }
    } catch (err) {
      console.warn('Failed to load feed', err);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 justify-items-center">
        {videos.map((video) => (
          <VideoCard
            key={video.id}
            video={video}
            onCommentClick={() => setSelectedVideo(video)}
          />
        ))}
      </div>

      {videos.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-500 text-lg">{t('feed.noVideosYet')}</p>
        </div>
      )}

      {selectedVideo && (
        <EnhancedCommentsModal
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  );
}
