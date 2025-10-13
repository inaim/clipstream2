import { useState } from 'react';
import { SwipeableVideoFeed } from './SwipeableVideoFeed';
import { MobileNavigation } from './MobileNavigation';
import { DiscoverPage } from './DiscoverPage';
import { MobileProfilePage } from './MobileProfilePage';
import { InboxPage } from './InboxPage';
import { UploadModal } from '../Upload/UploadModal';
import { AIAssistant } from '../AI/AIAssistant';

export function MobileApp() {
  const [currentTab, setCurrentTab] = useState<'home' | 'search' | 'upload' | 'inbox' | 'profile'>('home');
  const [feedType, setFeedType] = useState<'foryou' | 'following'>('foryou');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTabChange = (tab: 'home' | 'search' | 'upload' | 'inbox' | 'profile') => {
    if (tab === 'upload') {
      setShowUploadModal(true);
    } else {
      setCurrentTab(tab);
    }
  };

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

      <MobileNavigation currentTab={currentTab} onTabChange={handleTabChange} />

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      <AIAssistant />
    </div>
  );
}
