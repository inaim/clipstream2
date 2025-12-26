import { useState, useEffect } from 'react';
import { SwipeableVideoFeed } from './SwipeableVideoFeed';
import { MobileNavigation } from './MobileNavigation';
import { DiscoverPage } from './DiscoverPage';
import { MobileProfilePage } from './MobileProfilePage';
import { InboxPage } from './InboxPage';
import { UploadModal } from '../Upload/UploadModal';
import { AIAssistant } from '../AI/AIAssistant';
import { InstallPrompt } from '../PWA/InstallPrompt';

export function MobileApp() {
  const [currentTab, setCurrentTab] = useState<'home' | 'search' | 'upload' | 'inbox' | 'profile'>('home');
  const [feedType, setFeedType] = useState<'foryou' | 'following'>('foryou');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Unread counts for mobile inbox badge
  const [messagesUnread, setMessagesUnread] = useState<number>(0);
  const [notificationsUnread, setNotificationsUnread] = useState<number>(0);

  const handleTabChange = (tab: 'home' | 'search' | 'upload' | 'inbox' | 'profile') => {
    if (tab === 'upload') {
      setShowUploadModal(true);
    } else {
      setCurrentTab(tab);
    }
  };

  // fetch counts when mounting or refreshKey changes
  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
        // notifications
        try {
          const res = await fetch(`${API_BASE}/api/v1/notifications`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('clipstream_token')}` },
          });
          if (res.ok) {
            const data = await res.json();
            setNotificationsUnread(Array.isArray(data) ? data.filter((n: any) => !n.read).length : 0);
          }
        } catch (err) {
          console.error('Failed to fetch notification count (mobile)', err);
        }
        // messages
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
          console.error('Failed to fetch messages count (mobile)', err);
        }
      } catch (error) {
        console.error('Failed to fetch mobile unread counts', error);
      }
    };
    fetchCounts();
  }, [refreshKey]);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setCurrentTab('home');
  };

  return (
    <div className="fixed inset-0 bg-black">
      <div className="h-full">
        {currentTab === 'home' && (
          <SwipeableVideoFeed key={refreshKey} feedType={feedType} />
        )}

        {currentTab === 'search' && <DiscoverPage />}

        {currentTab === 'inbox' && <InboxPage />}

        {currentTab === 'profile' && <MobileProfilePage />}
      </div>

      <MobileNavigation currentTab={currentTab} onTabChange={handleTabChange} inboxUnread={messagesUnread + notificationsUnread} />

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      <AIAssistant />
      <InstallPrompt />
    </div>
  );
}
