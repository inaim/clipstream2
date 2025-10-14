import { useState } from 'react';
import { Header } from './Header';
import { VideoFeed } from '../Feed/VideoFeed';
import { ProfilePage } from '../Profile/ProfilePage';
import { UploadModal } from '../Upload/UploadModal';
import { SettingsPage } from '../Settings/SettingsPage';

export function MainApp() {
  const [currentView, setCurrentView] = useState<'feed' | 'profile' | 'settings'>('feed');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setCurrentView('feed');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        currentView={currentView === 'settings' ? 'profile' : currentView}
        onNavigate={setCurrentView}
        onUploadClick={() => setShowUploadModal(true)}
      />

      <main>
        {currentView === 'feed' ? (
          <VideoFeed key={refreshKey} />
        ) : currentView === 'settings' ? (
          <SettingsPage onClose={() => setCurrentView('profile')} />
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
