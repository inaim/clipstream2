import React, { useState, useEffect } from 'react';
import {
  Users,
  Video,
  TrendingUp,
  AlertCircle,
  Ban,
  CheckCircle,
  Eye,
  Download,
  Search,
  Filter,
  MoreVertical,
  Shield,
  Activity,
  DollarSign,
  Clock,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  avatar?: string;
  createdAt: string;
  status: 'active' | 'suspended' | 'banned';
  videoCount: number;
  followerCount: number;
  totalViews: number;
  totalLikes: number;
  lastActive: string;
}

interface VideoItem {
  id: string;
  title: string;
  creatorId: string;
  creatorUsername: string;
  uploadedAt: string;
  status: 'active' | 'processing' | 'flagged' | 'removed';
  views: number;
  likes: number;
  comments: number;
  shares: number;
  duration: number;
  flagCount: number;
}

interface Stats {
  totalUsers: number;
  activeUsers: number;
  totalVideos: number;
  totalViews: number;
  totalLikes: number;
  flaggedContent: number;
  revenue: number;
  growthRate: number;
}

export const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'videos' | 'reports'>('overview');
  const [users, setUsers] = useState<User[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalUsers: 0,
    activeUsers: 0,
    totalVideos: 0,
    totalViews: 0,
    totalLikes: 0,
    flaggedContent: 0,
    revenue: 0,
    growthRate: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const { t } = useLanguage();

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch('/api/admin/stats', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch users
      const usersRes = await fetch('/api/admin/users', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setUsers(usersData);
      }

      // Fetch videos
      const videosRes = await fetch('/api/admin/videos', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (videosRes.ok) {
        const videosData = await videosRes.json();
        setVideos(videosData);
      }
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
    }
  };

  const handleUserAction = async (userId: string, action: 'suspend' | 'ban' | 'activate') => {
    try {
      const res = await fetch(`/api/admin/users/${userId}/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        fetchAdminData();
      }
    } catch (error) {
      console.error(`Failed to ${action} user:`, error);
    }
  };

  const handleVideoAction = async (videoId: string, action: 'remove' | 'approve' | 'flag') => {
    try {
      const res = await fetch(`/api/admin/videos/${videoId}/${action}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        fetchAdminData();
      }
    } catch (error) {
      console.error(`Failed to ${action} video:`, error);
    }
  };

  const exportData = (type: 'users' | 'videos') => {
    const data = type === 'users' ? users : videos;
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}-${new Date().toISOString()}.csv`;
    a.click();
  };

  const convertToCSV = (data: any[]) => {
    if (data.length === 0) return '';
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map((item) => Object.values(item).join(','));
    return [headers, ...rows].join('\n');
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.displayName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || user.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const filteredVideos = videos.filter((video) => {
    const matchesSearch =
      video.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      video.creatorUsername.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || video.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['overview', 'users', 'videos', 'reports'].map((tab) => (
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
                title="Total Users"
                value={stats.totalUsers.toLocaleString()}
                icon={<Users className="w-6 h-6" />}
                color="blue"
                trend={`+${stats.growthRate}%`}
              />
              <StatCard
                title="Active Users"
                value={stats.activeUsers.toLocaleString()}
                icon={<Activity className="w-6 h-6" />}
                color="green"
              />
              <StatCard
                title="Total Videos"
                value={stats.totalVideos.toLocaleString()}
                icon={<Video className="w-6 h-6" />}
                color="purple"
              />
              <StatCard
                title="Total Views"
                value={stats.totalViews.toLocaleString()}
                icon={<Eye className="w-6 h-6" />}
                color="orange"
              />
              <StatCard
                title="Total Likes"
                value={stats.totalLikes.toLocaleString()}
                icon={<TrendingUp className="w-6 h-6" />}
                color="pink"
              />
              <StatCard
                title="Flagged Content"
                value={stats.flaggedContent.toLocaleString()}
                icon={<AlertCircle className="w-6 h-6" />}
                color="red"
              />
              <StatCard
                title="Revenue"
                value={`$${stats.revenue.toLocaleString()}`}
                icon={<DollarSign className="w-6 h-6" />}
                color="green"
              />
              <StatCard
                title="Avg. Session"
                value="24m"
                icon={<Clock className="w-6 h-6" />}
                color="indigo"
              />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">User Growth</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                  Chart placeholder - Integrate with your preferred charting library
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">Video Uploads</h3>
                <div className="h-64 flex items-center justify-center text-gray-400">
                  Chart placeholder - Integrate with your preferred charting library
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold">Recent Activity</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {/* Activity items would go here */}
                <div className="p-4 text-gray-500 text-center">No recent activity</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div>
            {/* Search and Filters */}
            <div className="bg-white p-4 rounded-lg shadow mb-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="banned">Banned</option>
                </select>
                <button
                  onClick={() => exportData('users')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Export</span>
                </button>
              </div>
            </div>

            {/* Users Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Videos
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Engagement
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Joined
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            {user.avatar ? (
                              <img className="h-10 w-10 rounded-full" src={user.avatar} alt="" />
                            ) : (
                              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                                {user.displayName.charAt(0)}
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{user.displayName}</div>
                            <div className="text-sm text-gray-500">@{user.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            user.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : user.status === 'suspended'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {user.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.videoCount}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>{user.totalViews.toLocaleString()} views</div>
                        <div>{user.totalLikes.toLocaleString()} likes</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedUser(user)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View
                          </button>
                          {user.status === 'active' && (
                            <button
                              onClick={() => handleUserAction(user.id, 'suspend')}
                              className="text-yellow-600 hover:text-yellow-900"
                            >
                              Suspend
                            </button>
                          )}
                          {user.status === 'suspended' && (
                            <button
                              onClick={() => handleUserAction(user.id, 'activate')}
                              className="text-green-600 hover:text-green-900"
                            >
                              Activate
                            </button>
                          )}
                          <button
                            onClick={() => handleUserAction(user.id, 'ban')}
                            className="text-red-600 hover:text-red-900"
                          >
                            Ban
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'videos' && (
          <div>
            {/* Search and Filters */}
            <div className="bg-white p-4 rounded-lg shadow mb-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search videos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="processing">Processing</option>
                  <option value="flagged">Flagged</option>
                  <option value="removed">Removed</option>
                </select>
                <button
                  onClick={() => exportData('videos')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Export</span>
                </button>
              </div>
            </div>

            {/* Videos Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredVideos.map((video) => (
                <div key={video.id} className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition">
                  <div className="aspect-video bg-gray-200 relative">
                    <video className="w-full h-full object-cover" src={`/api/playback/${video.id}`} />
                    {video.flagCount > 0 && (
                      <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-semibold">
                        {video.flagCount} flags
                      </div>
                    )}
                  </div>
                  <div className="p-4">
                    <h4 className="font-semibold text-sm mb-1 truncate">{video.title}</h4>
                    <p className="text-xs text-gray-500 mb-2">@{video.creatorUsername}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span>{video.views.toLocaleString()} views</span>
                      <span>{video.likes.toLocaleString()} likes</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleVideoAction(video.id, 'approve')}
                        className="flex-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleVideoAction(video.id, 'remove')}
                        className="flex-1 px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Flagged Content & Reports</h3>
            <div className="text-gray-500 text-center py-8">
              Reports section - Display user reports and flagged content here
            </div>
          </div>
        )}
      </div>
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
    orange: 'bg-orange-100 text-orange-600',
    pink: 'bg-pink-100 text-pink-600',
    red: 'bg-red-100 text-red-600',
    indigo: 'bg-indigo-100 text-indigo-600',
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
