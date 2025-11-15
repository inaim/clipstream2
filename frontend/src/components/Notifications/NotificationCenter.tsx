import React, { useState, useEffect } from 'react';
import {
  Bell,
  Heart,
  MessageCircle,
  UserPlus,
  Video,
  TrendingUp,
  Gift,
  Settings,
  Check,
  X,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface Notification {
  id: string;
  type: 'like' | 'comment' | 'follow' | 'mention' | 'video' | 'gift' | 'system';
  userId?: string;
  username?: string;
  displayName?: string;
  avatar?: string;
  content: string;
  videoId?: string;
  videoThumbnail?: string;
  timestamp: string;
  read: boolean;
}

export const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [activeTab, setActiveTab] = useState<'all' | 'likes' | 'comments' | 'follows'>('all');
  const { user } = useAuth();

  useEffect(() => {
    fetchNotifications();
    // Set up real-time notifications via WebSocket or SSE
    const eventSource = new EventSource(`/api/v1/notifications/stream?userId=${user?.id}`);
    eventSource.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      setNotifications((prev) => [notification, ...prev]);
    };

    return () => {
      eventSource.close();
    };
  }, [user?.id]);

  const fetchNotifications = async () => {
    try {
      const res = await fetch('/api/v1/notifications', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      setNotifications(
        notifications.map((notif) =>
          notif.id === notificationId ? { ...notif, read: true } : notif
        )
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch('/api/v1/notifications/read-all', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      setNotifications(notifications.map((notif) => ({ ...notif, read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await fetch(`/api/v1/notifications/${notificationId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      setNotifications(notifications.filter((notif) => notif.id !== notificationId));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'like':
        return <Heart className="w-5 h-5 text-red-500 fill-current" />;
      case 'comment':
        return <MessageCircle className="w-5 h-5 text-blue-500" />;
      case 'follow':
        return <UserPlus className="w-5 h-5 text-green-500" />;
      case 'video':
        return <Video className="w-5 h-5 text-purple-500" />;
      case 'gift':
        return <Gift className="w-5 h-5 text-pink-500" />;
      case 'system':
        return <TrendingUp className="w-5 h-5 text-orange-500" />;
      default:
        return <Bell className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = (now.getTime() - date.getTime()) / 1000;

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const mins = Math.floor(diffInSeconds / 60);
      return `${mins}m ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h ago`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const filteredNotifications = notifications.filter((notif) => {
    if (filter === 'unread' && notif.read) return false;
    if (activeTab === 'likes' && notif.type !== 'like') return false;
    if (activeTab === 'comments' && notif.type !== 'comment') return false;
    if (activeTab === 'follows' && notif.type !== 'follow') return false;
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="max-w-2xl mx-auto bg-white min-h-screen">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 z-10">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold">Notifications</h1>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-full transition flex items-center space-x-1"
                >
                  <Check className="w-4 h-4" />
                  <span>Mark all read</span>
                </button>
              )}
              <button className="p-2 hover:bg-gray-100 rounded-full transition">
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            {[
              { key: 'all', label: 'All' },
              { key: 'likes', label: 'Likes' },
              { key: 'comments', label: 'Comments' },
              { key: 'follows', label: 'Follows' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex-1 py-2 px-4 rounded-md font-medium text-sm transition ${
                  activeTab === tab.key
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Unread Filter */}
          <div className="flex items-center space-x-4 mt-3">
            <button
              onClick={() => setFilter('all')}
              className={`text-sm font-medium ${
                filter === 'all' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`text-sm font-medium ${
                filter === 'unread' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              Unread {unreadCount > 0 && `(${unreadCount})`}
            </button>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      <div className="divide-y divide-gray-200">
        {filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <Bell className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No notifications yet</h3>
            <p className="text-gray-500 text-center">
              When someone likes, comments, or follows you, you'll see it here.
            </p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`p-4 hover:bg-gray-50 transition cursor-pointer ${
                !notification.read ? 'bg-blue-50' : ''
              }`}
              onClick={() => !notification.read && markAsRead(notification.id)}
            >
              <div className="flex items-start space-x-3">
                {/* Avatar or Icon */}
                <div className="flex-shrink-0">
                  {notification.avatar ? (
                    <img
                      src={notification.avatar}
                      alt=""
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                      {getNotificationIcon(notification.type)}
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    {notification.displayName && (
                      <span className="font-semibold">{notification.displayName} </span>
                    )}
                    {notification.content}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{formatTimestamp(notification.timestamp)}</p>
                </div>

                {/* Video Thumbnail (if applicable) */}
                {notification.videoThumbnail && (
                  <div className="flex-shrink-0">
                    <img
                      src={notification.videoThumbnail}
                      alt=""
                      className="w-12 h-16 object-cover rounded"
                    />
                  </div>
                )}

                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteNotification(notification.id);
                  }}
                  className="flex-shrink-0 p-1 hover:bg-gray-200 rounded-full transition"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>

              {/* Unread Indicator */}
              {!notification.read && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-600" />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
