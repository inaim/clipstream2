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

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

  useEffect(() => {
    loadVideos();
  }, []);

  // Subscribe to global feed events so newly-created videos appear immediately
  useEffect(() => {
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
    const es = new EventSource(`${API_BASE}/api/videos/events/global`);

    const handleSSE = (ev: MessageEvent) => {
      try {
        const payload = JSON.parse(ev.data);

        // If publisher sends a wrapper { type: 'video_created', video: {...} }
        const type = payload.type || null;

        if (type === 'video_created') {
          const data = payload.video || {};
          const id = data.id || data.video_id || data.videoId;
          if (!id) return;

          const item = {
            id,
            video_url: data.cdn_url || data.cdnUrl || data.video_url || '',
            title: data.title || 'Untitled',
            likes_count: data.likes_count ?? 0,
            comments_count: data.comments_count ?? 0,
            shares_count: data.shares_count ?? 0,
            user_id: data.user_id || data.userId || '',
            profiles: data.profiles || data.creator || { display_name: data.title || 'Untitled', username: id, avatar_url: '' },
            status: data.status || 'active',
            processing_steps: data.processing_steps || undefined,
          } as any as Video;

          setVideos((prev) => {
            if (prev.some((v) => v.id === id)) return prev;
            return [item, ...prev];
          });
          return;
        }

        // Status updates: { type: 'status', status: 'processing', video_id: 'video:xyz', processing_steps: {...} }
        if (type === 'status' || payload.status) {
          const vid = payload.video_id || payload.videoId || payload.id;
          const status = payload.status || null;
          const steps = payload.processing_steps || payload.processingSteps || null;
          if (!vid) return;

          setVideos((prev) => {
            const castPrev: any[] = prev as any[];
            return castPrev.map((v: any) => {
              // ids may be strings like 'video:abc' or object shapes; normalize
              const existingId: any = typeof v.id === 'object' ? (v.id?.id || v.id) : v.id;
              if (!existingId) return v;
              if (existingId === vid || existingId === String(vid)) {
                return {
                  ...v,
                  status: status || v.status,
                  processing_steps: steps || v.processing_steps,
                } as any as Video;
              }
              return v;
            });
          });
          return;
        }

        // Fallback: treat payload as a raw video object
        const data = payload.video || payload;
        const id = data.id || data.video_id || data.videoId;
        if (!id) return;
        const item = {
          id,
          video_url: data.cdn_url || data.cdnUrl || data.video_url || '',
          title: data.title || 'Untitled',
          likes_count: data.likes_count ?? 0,
          comments_count: data.comments_count ?? 0,
          shares_count: data.shares_count ?? 0,
          user_id: data.user_id || data.userId || '',
          profiles: data.profiles || data.creator || { display_name: data.title || 'Untitled', username: id, avatar_url: '' },
          status: data.status || 'active',
        } as any as Video;

        setVideos((prev) => {
          if (prev.some((v) => v.id === id)) return prev;
          return [item, ...prev];
        });
      } catch (err) {
        console.warn('Failed to parse SSE payload', err);
      }
    };

    // listen for both named event and default message
  es.addEventListener('video_created', handleSSE as EventListener);
  es.addEventListener('message', handleSSE as EventListener);

    es.onerror = (err) => {
      // keep a light touch in production; devs can inspect logs
      console.warn('Global feed SSE error', err);
    };

    return () => {
      try {
        es.close();
      } catch (e) {
        /* ignore */
      }
    };
  }, []);

  const loadVideos = async () => {
    setLoading(true);
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 
           'http://localhost:8080';
    // For mock backend, fetch videos from API directly
    try {
      const res = await fetch(`${API_BASE}/api/v1/feed/for-you?user_id=` + (user?.user_id ?? 'user-a'));
      if (res.ok) {
        const json = await res.json();
        // Backend may return an array or an object with items/videos
        const list = Array.isArray(json) ? json : (json.items || json.videos || json);
        const items = (list || []).map((it: any) => ({
          id: it.id || it.video_id || it._id || it.record || '',
          video_url: it.cdn_url || it.cdnUrl || it.video_url || it.playback_url || '',
          title: it.title || it.name || 'Untitled',
          likes_count: it.likes_count ?? 0,
          comments_count: it.comments_count ?? 0,
          shares_count: it.shares_count ?? 0,
          user_id: it.user_id || it.creator?.id || '',
          profiles: it.profiles || it.creator || { display_name: it.title || it.name || 'Untitled', username: (it.creator?.username || it.user_id || '').toString(), avatar_url: it.creator?.avatar_url || '' },
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

  // Dashboard summary widget
  const latestVideo = videos[0];
  const latestStatus = latestVideo ? (latestVideo as any).status || 'N/A' : 'N/A';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Show dashboard/status widget only if user has uploaded videos */}
      {/* Only show dashboard/status if the latest video is uploaded by the current user */}
      {videos.length > 0 && latestVideo && user && latestVideo.user_id === user.user_id && (
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex-1">
              <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl shadow-lg p-6 flex items-center gap-6">
                <div className="flex flex-col items-center justify-center">
                  <div className="text-4xl font-extrabold text-white drop-shadow-lg">{videos.length}</div>
                  <div className="text-white/80 font-medium">Videos</div>
                </div>
                <div className="flex flex-col items-center justify-center">
                  <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#fff" fillOpacity="0.2"/><path d="M8 8h8v8H8V8z" fill="#fff"/></svg>
                  <div className="text-white/80 text-xs mt-1">Feed</div>
                </div>
                <div className="flex flex-col items-center justify-center">
                  <span className={`px-3 py-1 text-sm font-bold rounded-full shadow ${latestStatus === 'queued' ? 'bg-yellow-400 text-yellow-900' : latestStatus === 'processing' ? 'bg-orange-400 text-orange-900' : latestStatus === 'failed' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'}`}>{latestStatus.toUpperCase()}</span>
                  <span className="text-white/80 text-xs mt-1">Latest status</span>
                </div>
              </div>
            </div>
            <div className="flex items-center">
              <button
                className="px-5 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl shadow-lg hover:scale-105 transition-transform duration-200 flex items-center gap-2"
                onClick={loadVideos}
              >
                <svg className="animate-spin mr-2" width="20" height="20" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="#fff" strokeWidth="4" opacity="0.2"/><path d="M12 2a10 10 0 0 1 10 10" stroke="#fff" strokeWidth="2"/></svg>
                Refresh Feed
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dev-only: Seed demo video button to create a mock video and test SSE/feed updates */}
      {import.meta.env.DEV && (
        <div className="mb-4 text-right">
          <button
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl shadow-lg hover:scale-105 transition-transform duration-200"
            onClick={async () => {
              try {
                const resp = await fetch(`${API_BASE}/api/v1/feed/debug/seed-video`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ title: `Demo at ${new Date().toISOString()}` }),
                });
                if (!resp.ok) {
                  console.warn('Seed demo failed', await resp.text());
                }
              } catch (err) {
                console.warn('Seed demo error', err);
              }
            }}
          >
            Seed Demo Video
          </button>
        </div>
      )}

      <div
        className="rounded-2xl mb-8 p-2 sm:p-4 md:p-8 min-h-[40vh] w-full flex justify-center"
        style={{
          background: 'rgba(10,10,15,0.85)',
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          border: '1px solid rgba(255,255,255,0.08)'
        }}
      >
        <div className="w-full max-w-[420px] md:max-w-[520px] lg:max-w-[600px] flex flex-col items-center">
          {videos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onCommentClick={() => setSelectedVideo(video)}
            />
          ))}
        </div>
        {/* Desktop: show discussion/comments panel to the right */}
        {selectedVideo && (
          <div className="hidden lg:block ml-8 w-[340px] max-w-[30vw]">
            <EnhancedCommentsModal
              video={selectedVideo}
              onClose={() => setSelectedVideo(null)}
              asPanel
            />
          </div>
        )}
      </div>

      {videos.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <img src="https://undraw.co/api/illustrations/undraw_upload_re_pasx.svg" alt="No videos" className="w-40 h-40 mb-6 opacity-80" />
          <p className="text-2xl font-semibold text-gray-700 mb-2">No videos yet</p>
          <p className="text-base text-gray-400">Your uploads will appear here as soon as they're under review or processing.</p>
          <button
            className="mt-6 px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl shadow-lg hover:scale-105 transition-transform duration-200"
            onClick={loadVideos}
          >
            Refresh
          </button>
        </div>
      )}

      {/* Mobile: show comments as modal */}
      {selectedVideo && (
        <div className="lg:hidden">
          <EnhancedCommentsModal
            video={selectedVideo}
            onClose={() => setSelectedVideo(null)}
          />
        </div>
      )}
    </div>
  );
}
