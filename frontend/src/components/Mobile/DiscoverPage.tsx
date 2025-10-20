import { useState, useEffect } from 'react';
import { Search, TrendingUp, MapPin } from 'lucide-react';
import type { Database } from '../../lib/database.types';

type Video = Database['public']['Tables']['videos']['Row'];

export function DiscoverPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [trendingVideos, setTrendingVideos] = useState<Video[]>([]);
  const [nearbyVideos, setNearbyVideos] = useState<Video[]>([]);
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    loadTrendingVideos();
    requestLocation();
  }, []);

  useEffect(() => {
    if (userLocation) {
      loadNearbyVideos();
    }
  }, [userLocation]);

  const requestLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
        },
        (error) => {
          console.error('Location error:', error);
        }
      );
    }
  };

  const loadTrendingVideos = async () => {
    const { data } = await supabase
      .from('videos')
      .select('*')
      .order('views_count', { ascending: false })
      .limit(12);

    if (data) {
      setTrendingVideos(data);
    }
  };

  const loadNearbyVideos = async () => {
    if (!userLocation) return;

    const { data } = await supabase
      .from('videos')
      .select('*')
      .not('latitude', 'is', null)
      .not('longitude', 'is', null)
      .limit(12);

    if (data) {
      setNearbyVideos(data);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    const { data } = await supabase
      .from('videos')
      .select('*')
      .or(`title.ilike.%${searchQuery}%,description.ilike.%${searchQuery}%`)
      .limit(20);

    if (data) {
      setTrendingVideos(data);
    }
  };

  return (
    <div className="h-full bg-black text-white overflow-y-auto pb-20">
      <div className="sticky top-0 bg-black/95 backdrop-blur-sm z-10 p-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search videos, users, sounds..."
            className="w-full pl-12 pr-4 py-3 bg-gray-900 rounded-full text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-sky-blue"
          />
        </div>
      </div>

      <div className="px-4 py-4">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-sky-blue" />
          <h2 className="text-xl font-bold">Trending</h2>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-8">
          {trendingVideos.map((video) => (
            <div
              key={video.id}
              className="aspect-[9/16] bg-gray-900 rounded-lg overflow-hidden relative group"
            >
              <video
                src={video.video_url}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition">
                <div className="absolute bottom-2 left-2 right-2">
                  <p className="text-white text-xs font-semibold line-clamp-2">
                    {video.title}
                  </p>
                  <p className="text-gray-300 text-xs">
                    {(typeof video.views_count === 'number' && video.views_count !== null)
                      ? video.views_count.toLocaleString()
                      : '0'} views
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {nearbyVideos.length > 0 && (
          <>
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="w-5 h-5 text-blue-500" />
              <h2 className="text-xl font-bold">Nearby</h2>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {nearbyVideos.map((video) => (
                <div
                  key={video.id}
                  className="aspect-[9/16] bg-gray-900 rounded-lg overflow-hidden relative group"
                >
                  <video
                    src={video.video_url}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition">
                    <div className="absolute bottom-2 left-2 right-2">
                      <p className="text-white text-xs font-semibold line-clamp-2">
                        {video.title}
                      </p>
                      {video.location_name && (
                        <p className="text-gray-300 text-xs flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {video.location_name}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
