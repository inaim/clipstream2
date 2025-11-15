import React, { useState, useEffect } from 'react';
import {
  Video,
  TrendingUp,
  Eye,
  Heart,
  MessageCircle,
  Share2,
  Edit,
  Trash2,
  Download,
  Clock,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Users,
  DollarSign,
  Calendar,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';

interface VideoStats {
  id: string;
  title: string;
  thumbnail?: string;
  status: 'active' | 'processing' | 'failed' | 'draft';
  uploadedAt: string;
  duration: number;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  watchTime: number;
  engagementRate: number;
  revenue?: number;
}

interface AnalyticsData {
  totalViews: number;
  totalLikes: number;
  totalComments: number;
  totalShares: number;
  totalRevenue: number;
  avgEngagementRate: number;
  followerGrowth: number;
  topVideo: VideoStats | null;
}

export const UserDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'videos' | 'analytics'>('overview');
  const [videos, setVideos] = useState<VideoStats[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalViews: 0,
    totalLikes: 0,
    totalComments: 0,
    totalShares: 0,
    totalRevenue: 0,
    avgEngagementRate: 0,
    followerGrowth: 0,
    topVideo: null,
  });
  const [selectedVideo, setSelectedVideo] = useState<VideoStats | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const { t } = useLanguage();
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  const fetchDashboardData = async () => {
    try {
      // Fetch user's videos
      const videosRes = await fetch(`/api/v1/users/${user?.id}/videos`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (videosRes.ok) {
        const videosData = await videosRes.json();
        setVideos(videosData);
      }

      // Fetch analytics
      const analyticsRes = await fetch(`/api/v1/analytics?range=${timeRange}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json();
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const handleDeleteVideo = async (videoId: string) => {
    if (!confirm('Are you sure you want to delete this video? This action cannot be undone.')) {
      return;
    }

    try {
      const res = await fetch(`/api/videos/${videoId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        setVideos(videos.filter((v) => v.id !== videoId));
      }
    } catch (error) {
      console.error('Failed to delete video:', error);
    }
  };

  const handleDownloadVideo = async (videoId: string) => {
    try {
      const res = await fetch(`/api/videos/${videoId}/download`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `video-${videoId}.mp4`;
        a.click();
      }
    } catch (error) {
      console.error('Failed to download video:', error);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Creator Dashboard</h1>
              <p className="text-gray-500 mt-1">Manage your content and track your performance</p>
            </div>
            <div className="flex items-center space-x-3">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="all">All time</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['overview', 'videos', 'analytics'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                title="Total Views"
                value={formatNumber(analytics.totalViews)}
                icon={<Eye className="w-6 h-6" />}
                color="blue"
                trend="+12.5%"
              />
              <StatCard
                title="Total Likes"
                value={formatNumber(analytics.totalLikes)}
                icon={<Heart className="w-6 h-6" />}
                color="pink"
                trend="+8.3%"
              />
              <StatCard
                title="Engagement Rate"
                value={`${analytics.avgEngagementRate.toFixed(1)}%`}
                icon={<TrendingUp className="w-6 h-6" />}
                color="green"
                trend="+5.2%"
              />
              <StatCard
                title="Revenue"
                value={`$${analytics.totalRevenue.toLocaleString()}`}
                icon={<DollarSign className="w-6 h-6" />}
                color="purple"
                trend="+15.7%"
              />
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Top Performing Video */}
              {analytics.topVideo && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="text-lg font-semibold mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-orange-500" />
                    Top Performing Video
                  </h3>
                  <div className="flex items-start space-x-4">
                    <div className="w-32 h-20 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0">
                      {analytics.topVideo.thumbnail && (
                        <img
                          src={analytics.topVideo.thumbnail}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold mb-2">{analytics.topVideo.title}</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                        <div>{formatNumber(analytics.topVideo.views)} views</div>
                        <div>{formatNumber(analytics.topVideo.likes)} likes</div>
                        <div>{formatNumber(analytics.topVideo.comments)} comments</div>
                        <div>{analytics.topVideo.engagementRate.toFixed(1)}% engagement</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Activity */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-blue-500" />
                  Performance Summary
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Total Videos</span>
                    <span className="font-semibold">{videos.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Total Comments</span>
                    <span className="font-semibold">{formatNumber(analytics.totalComments)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Total Shares</span>
                    <span className="font-semibold">{formatNumber(analytics.totalShares)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Follower Growth</span>
                    <span className="font-semibold text-green-600">+{analytics.followerGrowth}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Videos */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Recent Videos</h3>
                <button
                  onClick={() => setActiveTab('videos')}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View all
                </button>
              </div>
              <div className="divide-y divide-gray-200">
                {videos.slice(0, 5).map((video) => (
                  <div key={video.id} className="p-4 hover:bg-gray-50 transition">
                    <div className="flex items-center space-x-4">
                      <div className="w-24 h-16 bg-gray-200 rounded overflow-hidden flex-shrink-0">
                        {video.thumbnail && (
                          <img src={video.thumbnail} alt="" className="w-full h-full object-cover" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 truncate">{video.title}</h4>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Eye className="w-4 h-4 mr-1" />
                            {formatNumber(video.views)}
                          </span>
                          <span className="flex items-center">
                            <Heart className="w-4 h-4 mr-1" />
                            {formatNumber(video.likes)}
                          </span>
                          <span className="flex items-center">
                            <MessageCircle className="w-4 h-4 mr-1" />
                            {formatNumber(video.comments)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            video.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : video.status === 'processing'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {video.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'videos' && (
          <div>
            {/* Videos Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {videos.map((video) => (
                <div
                  key={video.id}
                  className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition"
                >
                  <div className="aspect-video bg-gray-200 relative group">
                    {video.thumbnail ? (
                      <img src={video.thumbnail} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <video className="w-full h-full object-cover" src={`/api/playback/${video.id}`} />
                    )}
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition flex items-center justify-center">
                      <div className="opacity-0 group-hover:opacity-100 transition flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setSelectedVideo(video);
                            setShowEditModal(true);
                          }}
                          className="p-2 bg-white rounded-full hover:bg-gray-100 transition"
                          title="Edit"
                        >
                          <Edit className="w-5 h-5 text-gray-700" />
                        </button>
                        <button
                          onClick={() => handleDownloadVideo(video.id)}
                          className="p-2 bg-white rounded-full hover:bg-gray-100 transition"
                          title="Download"
                        >
                          <Download className="w-5 h-5 text-gray-700" />
                        </button>
                        <button
                          onClick={() => handleDeleteVideo(video.id)}
                          className="p-2 bg-white rounded-full hover:bg-red-50 transition"
                          title="Delete"
                        >
                          <Trash2 className="w-5 h-5 text-red-600" />
                        </button>
                      </div>
                    </div>
                    <div className="absolute top-2 right-2">
                      {video.status === 'active' ? (
                        <CheckCircle className="w-6 h-6 text-green-500" />
                      ) : video.status === 'processing' ? (
                        <Clock className="w-6 h-6 text-yellow-500" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-red-500" />
                      )}
                    </div>
                    <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                      {formatDuration(video.duration)}
                    </div>
                  </div>
                  <div className="p-4">
                    <h4 className="font-semibold text-sm mb-2 truncate">{video.title}</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-3">
                      <div className="flex items-center">
                        <Eye className="w-3 h-3 mr-1" />
                        {formatNumber(video.views)}
                      </div>
                      <div className="flex items-center">
                        <Heart className="w-3 h-3 mr-1" />
                        {formatNumber(video.likes)}
                      </div>
                      <div className="flex items-center">
                        <MessageCircle className="w-3 h-3 mr-1" />
                        {formatNumber(video.comments)}
                      </div>
                      <div className="flex items-center">
                        <Share2 className="w-3 h-3 mr-1" />
                        {formatNumber(video.shares)}
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(video.uploadedAt).toLocaleDateString()}
                    </div>
                    {video.revenue && (
                      <div className="mt-2 text-sm font-semibold text-green-600">
                        ${video.revenue.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {videos.length === 0 && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No videos yet</h3>
                <p className="text-gray-500 mb-6">Start creating content to see your videos here</p>
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Upload Video
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Video Performance Over Time</h3>
              <div className="h-80 flex items-center justify-center text-gray-400">
                Chart placeholder - Integrate with your preferred charting library (Chart.js, Recharts, etc.)
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Engagement Metrics</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                  Engagement chart placeholder
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Audience Demographics</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                  Demographics chart placeholder
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Edit Video Modal */}
      {showEditModal && selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <h2 className="text-xl font-bold mb-4">Edit Video</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  defaultValue={selectedVideo.title}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Add a description..."
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: string;
  trend?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, trend }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    pink: 'bg-pink-100 text-pink-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>{icon}</div>
        {trend && <span className="text-sm font-semibold text-green-600">{trend}</span>}
      </div>
      <h3 className="text-gray-500 text-sm font-medium mb-1">{title}</h3>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
};
