import { useState } from 'react';
import { Header } from './Header';
import { VideoFeed } from '../Feed/VideoFeed';
import { ProfilePage } from '../Profile/ProfilePage';
import { UploadModal } from '../Upload/UploadModal';

export function MainApp() {
  const [currentView, setCurrentView] = useState<'feed' | 'profile'>('feed');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setCurrentView('feed');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        currentView={currentView}
        onNavigate={setCurrentView}
        onUploadClick={() => setShowUploadModal(true)}
      />

      <main>
        {currentView === 'feed' ? (
          <VideoFeed key={refreshKey} />
        ) : (
          <ProfilePage />
        )}
      </main>

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}
    </div>
  );
}
