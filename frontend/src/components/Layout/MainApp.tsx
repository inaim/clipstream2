import { useState } from 'react';
import { Header } from './Header';
import { VideoFeed } from '../Feed/VideoFeed';
import { ProfilePage } from '../Profile/ProfilePage';
import { UploadModal } from '../Upload/UploadModal';
import { SettingsPage } from '../Settings/SettingsPage';
import { SwipeableVideoFeed } from '../Mobile/SwipeableVideoFeed';
import { BottomNavigation } from './BottomNavigation';

export function MainApp() {
  // Simple mobile detection (can be improved with a hook or library)
  const isMobile = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(max-width: 640px)').matches;
  const [currentView, setCurrentView] = useState<'feed' | 'profile' | 'settings'>('feed');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setCurrentView('feed');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
      {/* Hide Header for now, move nav to bottom for all devices */}

      <main className="flex-1 w-full max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
        {currentView === 'feed' ? (
          isMobile ? (
            <SwipeableVideoFeed feedType="foryou" key={refreshKey} />
          ) : (
            <div className="flex flex-row gap-8 min-h-[60vh]">
              {/* Left side: reserved for widgets, user info, or left empty for minimalism */}
              <div className="hidden lg:block flex-1" />
              {/* Right side: video feed */}
              <div className="w-full max-w-2xl ml-auto">
                <VideoFeed key={refreshKey} />
              </div>
            </div>
          )
        ) : currentView === 'settings' ? (
          <SettingsPage onClose={() => setCurrentView('profile')} />
        ) : (
          <ProfilePage />
        )}
      </main>

      {/* Bottom navigation for all devices */}
      <BottomNavigation
        currentView={currentView}
        onNavigate={(view) => {
          window.scrollTo({ top: 0, behavior: 'smooth' });
          setShowUploadModal(false);
          setCurrentView(view);
        }}
        onUploadClick={() => setShowUploadModal(true)}
      />

      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="w-full max-w-md mx-auto p-2 sm:p-0">
            <UploadModal
              onClose={() => setShowUploadModal(false)}
              onSuccess={handleUploadSuccess}
            />
          </div>
        </div>
      )}
    </div>
  );
}
