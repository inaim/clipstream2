import { useState, useEffect } from 'react';
import { VideoFeed } from '../Feed/VideoFeed';
import { ProfilePage } from '../Profile/ProfilePage';
import { UploadModal } from '../Upload/UploadModal';
import { SettingsPage } from '../Settings/SettingsPage';
import { SwipeableVideoFeed } from '../Mobile/SwipeableVideoFeed';
import { BottomNavigation } from './BottomNavigation';
import { InterestSelection } from '../Onboarding/InterestSelection';
import { AdminDashboard } from '../Admin/AdminDashboard';
import { UserDashboard } from '../Dashboard/UserDashboard';
import { SearchAndDiscover } from '../Search/SearchAndDiscover';
import { DirectMessages } from '../Messaging/DirectMessages';
import { NotificationCenter } from '../Notifications/NotificationCenter';
import { VideoEditor } from '../VideoEditor/VideoEditor';
import { SoundLibrary } from '../Sound/SoundLibrary';
import { useAuth } from '../../contexts/AuthContext';
import {
  Home,
  Search,
  PlusSquare,
  MessageCircle,
  User,
  Bell,
  BarChart3,
  Shield,
} from 'lucide-react';

type ViewType =
  | 'feed'
  | 'search'
  | 'profile'
  | 'settings'
  | 'messages'
  | 'notifications'
  | 'dashboard'
  | 'admin';

export function EnhancedMainApp() {
  const { user } = useAuth();
  const isMobile =
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(max-width: 640px)').matches;

  const [currentView, setCurrentView] = useState<ViewType>('feed');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showInterestSelection, setShowInterestSelection] = useState(false);
  const [showVideoEditor, setShowVideoEditor] = useState(false);
  const [showSoundLibrary, setShowSoundLibrary] = useState(false);
  const [selectedVideoFile, setSelectedVideoFile] = useState<File | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [userHasSelectedInterests, setUserHasSelectedInterests] = useState(false);

  // Unread counts for badges
  const [messagesUnread, setMessagesUnread] = useState<number>(0);
  const [notificationsUnread, setNotificationsUnread] = useState<number>(0);

  useEffect(() => {
    // Check if user has selected interests
    checkUserInterests();
    // fetch initial unread counts
    fetchUnreadCounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Refresh unread counts when returning to feed or when refreshKey changes
  useEffect(() => {
    fetchUnreadCounts();
  }, [refreshKey]);

  const fetchUnreadCounts = async () => {
    if (!user?.id) {
      setMessagesUnread(0);
      setNotificationsUnread(0);
      return;
    }

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

      // Notifications unread
      try {
        const res = await fetch(`${API_BASE}/api/v1/notifications`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('clipstream_token')}` },
        });
        if (res.ok) {
          const data = await res.json();
          const unread = Array.isArray(data) ? data.filter((n: any) => !n.read).length : 0;
          setNotificationsUnread(unread);
        }
      } catch (err) {
        console.error('Failed to fetch notification count', err);
      }

      // Messages unread (sum of conversation unread counts)
      try {
        const res2 = await fetch(`${API_BASE}/api/v1/messages/conversations`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('clipstream_token')}` },
        });
        if (res2.ok) {
          const convs = await res2.json();
          const unreadMsgs = (convs || []).reduce((acc: number, c: any) => acc + (c.unread_count || c.unreadCount || 0), 0);
          setMessagesUnread(unreadMsgs);
        }
      } catch (err) {
        console.error('Failed to fetch messages count', err);
      }
    } catch (error) {
      console.error('Failed to fetch unread counts:', error);
    }
  };

  const checkUserInterests = async () => {
    try {
      const res = await fetch(`/api/v1/users/${user?.id}/interests`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setUserHasSelectedInterests(data.hasInterests);
        if (!data.hasInterests) {
          setShowInterestSelection(true);
        }
      }
    } catch (error) {
      console.error('Failed to check user interests:', error);
    }
  };

  const handleInterestsComplete = async (interests: string[]) => {
    try {
      await fetch(`/api/v1/users/${user?.id}/interests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
        body: JSON.stringify({ interests }),
      });
      setShowInterestSelection(false);
      setUserHasSelectedInterests(true);
    } catch (error) {
      console.error('Failed to save interests:', error);
    }
  };

  const handleUploadSuccess = () => {
    setRefreshKey((prev) => prev + 1);
    setCurrentView('feed');
    setShowUploadModal(false);
  };

  const handleUploadWithEditor = (file: File) => {
    setSelectedVideoFile(file);
    setShowUploadModal(false);
    setShowVideoEditor(true);
  };

  const handleEditorSave = (editedVideo: Blob, metadata: any) => {
    // Here you would upload the edited video with metadata
    console.log('Edited video:', editedVideo, 'Metadata:', metadata);
    setShowVideoEditor(false);
    setSelectedVideoFile(null);
    handleUploadSuccess();
  };

  const handleSoundSelect = (sound: any) => {
    console.log('Selected sound:', sound);
    setShowSoundLibrary(false);
  };

  // Show interest selection modal for new users
  if (showInterestSelection && !userHasSelectedInterests) {
    return (
      <InterestSelection
        onComplete={handleInterestsComplete}
        onSkip={() => setShowInterestSelection(false)}
      />
    );
  }

  const renderView = () => {
    switch (currentView) {
      case 'feed':
        return isMobile ? (
          <SwipeableVideoFeed feedType="foryou" key={refreshKey} />
        ) : (
          <div className="flex flex-row gap-8 min-h-[60vh]">
            <div className="hidden lg:block flex-1" />
            <div className="w-full max-w-2xl ml-auto">
              <VideoFeed key={refreshKey} />
            </div>
          </div>
        );

      case 'search':
        return <SearchAndDiscover />;

      case 'messages':
        return <DirectMessages />;

      case 'notifications':
        return <NotificationCenter />;

      case 'dashboard':
        return <UserDashboard />;

      case 'admin':
        // Check if user is admin
        return user?.role === 'admin' ? (
          <AdminDashboard />
        ) : (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have permission to access this page.</p>
          </div>
        );

      case 'settings':
        return <SettingsPage onClose={() => setCurrentView('profile')} />;

      case 'profile':
      default:
        return <ProfilePage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
      {/* Main Content */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
        {renderView()}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40">
        <div className="max-w-7xl mx-auto px-2 sm:px-4">
          <div className="flex items-center justify-around py-2">
            <button
              onClick={() => setCurrentView('feed')}
              className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition ${
                currentView === 'feed'
                  ? 'text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Home className="w-6 h-6" />
              <span className="text-xs font-medium">Home</span>
            </button>

            <button
              onClick={() => setCurrentView('search')}
              className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition ${
                currentView === 'search'
                  ? 'text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Search className="w-6 h-6" />
              <span className="text-xs font-medium">Discover</span>
            </button>

            <button
              onClick={() => setShowUploadModal(true)}
              className="relative -top-4 flex flex-col items-center space-y-1"
            >
              <div className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition">
                <PlusSquare className="w-7 h-7 text-white" />
              </div>
            </button>

            <button
              onClick={() => {
                setCurrentView('messages');
                // optimistically clear unread badge when user opens messages
                setMessagesUnread(0);
              }}
              className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition relative ${
                currentView === 'messages'
                  ? 'text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <MessageCircle className="w-6 h-6" />
              <span className="text-xs font-medium">Messages</span>
              {/* Unread badge (show only when there are unread messages) */}
              {messagesUnread > 0 && (
                <span className="absolute top-1 right-2 min-w-[1rem] h-4 bg-red-500 rounded-full flex items-center justify-center text-xs text-white font-semibold px-1">
                  {messagesUnread > 9 ? '9+' : messagesUnread}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                setCurrentView('notifications');
                // optimistically clear unread badge when user opens notifications
                setNotificationsUnread(0);
              }}
              className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition relative ${
                currentView === 'notifications'
                  ? 'text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Bell className="w-6 h-6" />
              <span className="text-xs font-medium">Inbox</span>
              {/* Notification badge (show only when there are unread notifications) */}
              {notificationsUnread > 0 && (
                <span className="absolute top-1 right-2 min-w-[1rem] h-4 bg-red-500 rounded-full flex items-center justify-center text-xs text-white font-semibold px-1">
                  {notificationsUnread > 9 ? '9+' : notificationsUnread}
                </span>
              )}
            </button>

            <button
              onClick={() => setCurrentView('profile')}
              className={`flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition ${
                currentView === 'profile'
                  ? 'text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <User className="w-6 h-6" />
              <span className="text-xs font-medium">Profile</span>
            </button>
          </div>

          {/* Secondary Navigation Row (Desktop) */}
          {!isMobile && (
            <div className="hidden md:flex items-center justify-center space-x-4 pb-2 border-t border-gray-100 pt-2">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                  currentView === 'dashboard'
                    ? 'bg-blue-100 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BarChart3 className="w-5 h-5" />
                <span className="text-sm font-medium">Dashboard</span>
              </button>

              {user?.role === 'admin' && (
                <button
                  onClick={() => setCurrentView('admin')}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${
                    currentView === 'admin'
                      ? 'bg-blue-100 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Shield className="w-5 h-5" />
                  <span className="text-sm font-medium">Admin</span>
                </button>
              )}
            </div>
          )}
        </div>
      </nav>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="w-full max-w-md mx-auto p-2 sm:p-0">
            <UploadModal
              onClose={() => setShowUploadModal(false)}
              onSuccess={handleUploadSuccess}
              onEditBeforeUpload={handleUploadWithEditor}
            />
          </div>
        </div>
      )}

      {/* Video Editor */}
      {showVideoEditor && selectedVideoFile && (
        <VideoEditor
          videoFile={selectedVideoFile}
          onSave={handleEditorSave}
          onCancel={() => {
            setShowVideoEditor(false);
            setSelectedVideoFile(null);
          }}
        />
      )}

      {/* Sound Library */}
      {showSoundLibrary && (
        <SoundLibrary
          onSelect={handleSoundSelect}
          onClose={() => setShowSoundLibrary(false)}
        />
      )}
    </div>
  );
}
