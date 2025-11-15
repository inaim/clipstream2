import React, { useState, useEffect, useRef } from 'react';
import {
  Music,
  Search,
  Play,
  Pause,
  TrendingUp,
  Clock,
  Heart,
  Check,
  Volume2,
  VolumeX,
} from 'lucide-react';

interface Sound {
  id: string;
  title: string;
  artist: string;
  duration: number;
  coverArt?: string;
  audioUrl: string;
  category: string;
  isPopular: boolean;
  usageCount: number;
  isFavorite?: boolean;
}

interface SoundCategory {
  id: string;
  name: string;
  emoji: string;
}

const categories: SoundCategory[] = [
  { id: 'trending', name: 'Trending', emoji: '🔥' },
  { id: 'pop', name: 'Pop', emoji: '🎵' },
  { id: 'hiphop', name: 'Hip Hop', emoji: '🎤' },
  { id: 'electronic', name: 'Electronic', emoji: '🎹' },
  { id: 'rock', name: 'Rock', emoji: '🎸' },
  { id: 'jazz', name: 'Jazz', emoji: '🎺' },
  { id: 'classical', name: 'Classical', emoji: '🎻' },
  { id: 'country', name: 'Country', emoji: '🤠' },
  { id: 'latin', name: 'Latin', emoji: '💃' },
  { id: 'indie', name: 'Indie', emoji: '🌟' },
  { id: 'favorites', name: 'Favorites', emoji: '❤️' },
];

interface SoundLibraryProps {
  onSelect: (sound: Sound) => void;
  onClose: () => void;
}

export const SoundLibrary: React.FC<SoundLibraryProps> = ({ onSelect, onClose }) => {
  const [sounds, setSounds] = useState<Sound[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('trending');
  const [searchQuery, setSearchQuery] = useState('');
  const [playingSound, setPlayingSound] = useState<Sound | null>(null);
  const [selectedSound, setSelectedSound] = useState<Sound | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    fetchSounds(selectedCategory);
  }, [selectedCategory]);

  const fetchSounds = async (category: string) => {
    try {
      const res = await fetch(`/api/v1/sounds?category=${category}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSounds(data);
      }
    } catch (error) {
      console.error('Failed to fetch sounds:', error);
    }
  };

  const searchSounds = async () => {
    if (!searchQuery.trim()) {
      fetchSounds(selectedCategory);
      return;
    }

    try {
      const res = await fetch(`/api/v1/sounds/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSounds(data);
      }
    } catch (error) {
      console.error('Failed to search sounds:', error);
    }
  };

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery) {
        searchSounds();
      }
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const togglePlay = (sound: Sound) => {
    if (playingSound?.id === sound.id) {
      audioRef.current?.pause();
      setPlayingSound(null);
    } else {
      if (audioRef.current) {
        audioRef.current.src = sound.audioUrl;
        audioRef.current.play();
        setPlayingSound(sound);
      }
    }
  };

  const toggleFavorite = async (soundId: string) => {
    try {
      const sound = sounds.find((s) => s.id === soundId);
      const isFavorite = sound?.isFavorite;

      const res = await fetch(`/api/v1/sounds/${soundId}/favorite`, {
        method: isFavorite ? 'DELETE' : 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });

      if (res.ok) {
        setSounds(
          sounds.map((s) => (s.id === soundId ? { ...s, isFavorite: !isFavorite } : s))
        );
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleSelect = (sound: Sound) => {
    setSelectedSound(sound);
    onSelect(sound);
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatUsageCount = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        muted={isMuted}
        onEnded={() => setPlayingSound(null)}
      />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Sound Library</h2>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-full transition"
          >
            Close
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search songs, artists..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="border-b border-gray-200 px-4 py-3 overflow-x-auto hide-scrollbar">
        <div className="flex space-x-2">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`flex-shrink-0 px-4 py-2 rounded-full font-medium text-sm transition ${
                selectedCategory === category.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span className="mr-1">{category.emoji}</span>
              {category.name}
            </button>
          ))}
        </div>
      </div>

      {/* Sounds List */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-4 space-y-2">
          {sounds.map((sound) => (
            <div
              key={sound.id}
              className={`bg-white border rounded-lg p-4 hover:shadow-md transition ${
                selectedSound?.id === sound.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center space-x-4">
                {/* Play Button */}
                <button
                  onClick={() => togglePlay(sound)}
                  className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-pink-500 to-purple-500 rounded-full flex items-center justify-center text-white hover:scale-105 transition"
                >
                  {playingSound?.id === sound.id ? (
                    <Pause className="w-6 h-6" />
                  ) : (
                    <Play className="w-6 h-6 ml-0.5" />
                  )}
                </button>

                {/* Sound Info */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-gray-900 truncate">{sound.title}</h4>
                  <p className="text-sm text-gray-600 truncate">{sound.artist}</p>
                  <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                    <span className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDuration(sound.duration)}
                    </span>
                    <span className="flex items-center">
                      <Music className="w-3 h-3 mr-1" />
                      {formatUsageCount(sound.usageCount)} videos
                    </span>
                    {sound.isPopular && (
                      <span className="flex items-center text-orange-500">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        Trending
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    onClick={() => toggleFavorite(sound.id)}
                    className="p-2 hover:bg-gray-100 rounded-full transition"
                  >
                    <Heart
                      className={`w-5 h-5 ${
                        sound.isFavorite ? 'text-red-500 fill-current' : 'text-gray-400'
                      }`}
                    />
                  </button>
                  <button
                    onClick={() => handleSelect(sound)}
                    className={`px-6 py-2 rounded-full font-semibold transition ${
                      selectedSound?.id === sound.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {selectedSound?.id === sound.id ? (
                      <span className="flex items-center space-x-1">
                        <Check className="w-4 h-4" />
                        <span>Selected</span>
                      </span>
                    ) : (
                      'Use'
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {sounds.length === 0 && (
            <div className="text-center py-12">
              <Music className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchQuery ? 'No sounds found' : 'No sounds available in this category'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Bar */}
      {selectedSound && (
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-purple-500 rounded-lg flex items-center justify-center">
                <Music className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-semibold">{selectedSound.title}</div>
                <div className="text-sm text-gray-600">{selectedSound.artist}</div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Mute Toggle (Floating) */}
      {playingSound && (
        <button
          onClick={() => setIsMuted(!isMuted)}
          className="fixed bottom-24 right-6 w-12 h-12 bg-gray-900 bg-opacity-75 rounded-full flex items-center justify-center text-white hover:bg-opacity-90 transition"
        >
          {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
        </button>
      )}
    </div>
  );
};
