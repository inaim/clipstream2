import React, { useState, useEffect } from 'react';
import {
  Search,
  TrendingUp,
  Hash,
  Music,
  Users,
  Play,
  Heart,
  Eye,
  Flame,
  Sparkles,
  Clock,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface SearchResult {
  type: 'user' | 'video' | 'hashtag' | 'sound';
  id: string;
  title: string;
  subtitle?: string;
  thumbnail?: string;
  avatar?: string;
  stats?: {
    views?: number;
    likes?: number;
    videos?: number;
    followers?: number;
  };
}

interface TrendingHashtag {
  id: string;
  name: string;
  videoCount: number;
  viewCount: number;
  isNew?: boolean;
}

interface TrendingSound {
  id: string;
  title: string;
  artist: string;
  videoCount: number;
  thumbnail?: string;
}

interface TrendingCreator {
  id: string;
  username: string;
  displayName: string;
  avatar?: string;
  followerCount: number;
  isVerified?: boolean;
}

export const SearchAndDiscover: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [activeTab, setActiveTab] = useState<'trending' | 'hashtags' | 'sounds' | 'creators'>('trending');
  const [trendingHashtags, setTrendingHashtags] = useState<TrendingHashtag[]>([]);
  const [trendingSounds, setTrendingSounds] = useState<TrendingSound[]>([]);
  const [trendingCreators, setTrendingCreators] = useState<TrendingCreator[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    fetchTrendingData();
  }, []);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      performSearch();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const fetchTrendingData = async () => {
    try {
      // Fetch trending hashtags
      const hashtagsRes = await fetch('/api/v1/trending/hashtags');
      if (hashtagsRes.ok) {
        const hashtags = await hashtagsRes.json();
        setTrendingHashtags(hashtags);
      }

      // Fetch trending sounds
      const soundsRes = await fetch('/api/v1/trending/sounds');
      if (soundsRes.ok) {
        const sounds = await soundsRes.json();
        setTrendingSounds(sounds);
      }

      // Fetch trending creators
      const creatorsRes = await fetch('/api/v1/trending/creators');
      if (creatorsRes.ok) {
        const creators = await creatorsRes.json();
        setTrendingCreators(creators);
      }
    } catch (error) {
      console.error('Failed to fetch trending data:', error);
    }
  };

  const performSearch = async () => {
    setIsSearching(true);
    try {
      const res = await fetch(`/api/v1/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const results = await res.json();
        setSearchResults(results);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Search Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search users, videos, hashtags, sounds..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
            />
            {isSearching && (
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {searchQuery.length >= 2 ? (
          // Search Results
          <div>
            <h2 className="text-lg font-semibold mb-4">Search Results</h2>
            {searchResults.length === 0 && !isSearching && (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No results found for "{searchQuery}"</p>
              </div>
            )}
            <div className="space-y-3">
              {searchResults.map((result) => (
                <div
                  key={`${result.type}-${result.id}`}
                  className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer"
                >
                  <div className="flex items-center space-x-4">
                    {result.type === 'user' && (
                      <>
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                          {result.avatar ? (
                            <img src={result.avatar} alt="" className="w-full h-full rounded-full" />
                          ) : (
                            result.title.charAt(0)
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold">{result.title}</div>
                          <div className="text-sm text-gray-500">@{result.subtitle}</div>
                          {result.stats?.followers && (
                            <div className="text-sm text-gray-500">
                              {formatNumber(result.stats.followers)} followers
                            </div>
                          )}
                        </div>
                        <Users className="w-5 h-5 text-gray-400" />
                      </>
                    )}
                    {result.type === 'video' && (
                      <>
                        <div className="w-20 h-14 rounded bg-gray-200 flex-shrink-0 overflow-hidden">
                          {result.thumbnail && (
                            <img src={result.thumbnail} alt="" className="w-full h-full object-cover" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold line-clamp-2">{result.title}</div>
                          {result.subtitle && <div className="text-sm text-gray-500">{result.subtitle}</div>}
                          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                            {result.stats?.views && (
                              <span className="flex items-center">
                                <Eye className="w-3 h-3 mr-1" />
                                {formatNumber(result.stats.views)}
                              </span>
                            )}
                            {result.stats?.likes && (
                              <span className="flex items-center">
                                <Heart className="w-3 h-3 mr-1" />
                                {formatNumber(result.stats.likes)}
                              </span>
                            )}
                          </div>
                        </div>
                        <Play className="w-5 h-5 text-gray-400" />
                      </>
                    )}
                    {result.type === 'hashtag' && (
                      <>
                        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <Hash className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold">#{result.title}</div>
                          {result.stats?.videos && (
                            <div className="text-sm text-gray-500">
                              {formatNumber(result.stats.videos)} videos
                            </div>
                          )}
                        </div>
                        <Hash className="w-5 h-5 text-gray-400" />
                      </>
                    )}
                    {result.type === 'sound' && (
                      <>
                        <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center flex-shrink-0">
                          <Music className="w-6 h-6 text-pink-600" />
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold">{result.title}</div>
                          {result.subtitle && <div className="text-sm text-gray-500">{result.subtitle}</div>}
                          {result.stats?.videos && (
                            <div className="text-sm text-gray-500">
                              {formatNumber(result.stats.videos)} videos
                            </div>
                          )}
                        </div>
                        <Music className="w-5 h-5 text-gray-400" />
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          // Discover / Trending Content
          <div>
            {/* Tabs */}
            <div className="flex space-x-1 mb-6 bg-gray-200 p-1 rounded-lg">
              {[
                { key: 'trending', label: 'Trending', icon: <Flame className="w-4 h-4" /> },
                { key: 'hashtags', label: 'Hashtags', icon: <Hash className="w-4 h-4" /> },
                { key: 'sounds', label: 'Sounds', icon: <Music className="w-4 h-4" /> },
                { key: 'creators', label: 'Creators', icon: <Users className="w-4 h-4" /> },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md font-medium text-sm transition ${
                    activeTab === tab.key
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Trending Tab */}
            {activeTab === 'trending' && (
              <div className="space-y-6">
                {/* Trending Hashtags */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-orange-500" />
                    Trending Hashtags
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {trendingHashtags.slice(0, 6).map((hashtag, index) => (
                      <div
                        key={hashtag.id}
                        className="bg-gradient-to-br from-blue-500 to-purple-600 p-4 rounded-lg text-white cursor-pointer hover:scale-105 transition transform"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <Hash className="w-5 h-5" />
                            <span className="font-bold">#{index + 1}</span>
                          </div>
                          {hashtag.isNew && (
                            <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs font-semibold">
                              NEW
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-lg mb-1">#{hashtag.name}</h4>
                        <div className="text-sm opacity-90">
                          {formatNumber(hashtag.viewCount)} views • {formatNumber(hashtag.videoCount)} videos
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trending Sounds */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Music className="w-5 h-5 mr-2 text-pink-500" />
                    Trending Sounds
                  </h3>
                  <div className="space-y-3">
                    {trendingSounds.slice(0, 5).map((sound) => (
                      <div
                        key={sound.id}
                        className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer"
                      >
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 rounded bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                            <Music className="w-6 h-6 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold">{sound.title}</div>
                            <div className="text-sm text-gray-500">{sound.artist}</div>
                            <div className="text-sm text-gray-400 mt-1">
                              {formatNumber(sound.videoCount)} videos
                            </div>
                          </div>
                          <Play className="w-8 h-8 text-gray-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trending Creators */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Sparkles className="w-5 h-5 mr-2 text-yellow-500" />
                    Trending Creators
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {trendingCreators.slice(0, 6).map((creator) => (
                      <div
                        key={creator.id}
                        className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                            {creator.avatar ? (
                              <img src={creator.avatar} alt="" className="w-full h-full rounded-full" />
                            ) : (
                              creator.displayName.charAt(0)
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold truncate flex items-center">
                              {creator.displayName}
                              {creator.isVerified && (
                                <svg className="w-4 h-4 ml-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path
                                    fillRule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              )}
                            </div>
                            <div className="text-sm text-gray-500 truncate">@{creator.username}</div>
                            <div className="text-sm text-gray-400">
                              {formatNumber(creator.followerCount)} followers
                            </div>
                          </div>
                          <button className="px-4 py-1.5 bg-blue-600 text-white rounded-full text-sm font-semibold hover:bg-blue-700 transition">
                            Follow
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Hashtags Tab */}
            {activeTab === 'hashtags' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {trendingHashtags.map((hashtag, index) => (
                  <div
                    key={hashtag.id}
                    className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer border-l-4 border-blue-500"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Hash className="w-6 h-6 text-blue-600" />
                        <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                      </div>
                      {hashtag.isNew && (
                        <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-semibold">
                          NEW
                        </span>
                      )}
                    </div>
                    <h4 className="font-bold text-xl mb-2">#{hashtag.name}</h4>
                    <div className="text-sm text-gray-600">
                      <div>{formatNumber(hashtag.viewCount)} views</div>
                      <div>{formatNumber(hashtag.videoCount)} videos</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Sounds Tab */}
            {activeTab === 'sounds' && (
              <div className="space-y-3">
                {trendingSounds.map((sound, index) => (
                  <div
                    key={sound.id}
                    className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-bold text-gray-400 w-8">#{index + 1}</div>
                      <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                        <Music className="w-8 h-8 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="font-bold text-lg">{sound.title}</div>
                        <div className="text-gray-600">{sound.artist}</div>
                        <div className="text-sm text-gray-500 mt-1">
                          {formatNumber(sound.videoCount)} videos
                        </div>
                      </div>
                      <button className="px-6 py-2 bg-pink-600 text-white rounded-full font-semibold hover:bg-pink-700 transition">
                        Use Sound
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Creators Tab */}
            {activeTab === 'creators' && (
              <div className="space-y-3">
                {trendingCreators.map((creator, index) => (
                  <div
                    key={creator.id}
                    className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition cursor-pointer"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-bold text-gray-400 w-8">#{index + 1}</div>
                      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                        {creator.avatar ? (
                          <img src={creator.avatar} alt="" className="w-full h-full rounded-full" />
                        ) : (
                          creator.displayName.charAt(0)
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-bold text-lg flex items-center">
                          {creator.displayName}
                          {creator.isVerified && (
                            <svg className="w-5 h-5 ml-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                clipRule="evenodd"
                              />
                            </svg>
                          )}
                        </div>
                        <div className="text-gray-600">@{creator.username}</div>
                        <div className="text-sm text-gray-500">{formatNumber(creator.followerCount)} followers</div>
                      </div>
                      <button className="px-6 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition">
                        Follow
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
