import { Home, Upload, User as UserIcon } from 'lucide-react';

interface BottomNavigationProps {
  currentView: 'feed' | 'profile' | 'settings';
  onNavigate: (view: 'feed' | 'profile' | 'settings') => void;
  onUploadClick: () => void;
}

export function BottomNavigation({ currentView, onNavigate, onUploadClick }: BottomNavigationProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow flex justify-around items-center h-16">
      <button
        className={`flex flex-col items-center justify-center px-4 py-2 ${currentView === 'feed' ? 'text-blue-600' : 'text-gray-500'}`}
        onClick={() => onNavigate('feed')}
      >
        <Home className="w-6 h-6 mb-1" />
        <span className="text-xs">Home</span>
      </button>
      <button
        className="flex flex-col items-center justify-center px-4 py-2 text-gray-500"
        onClick={onUploadClick}
      >
        <Upload className="w-6 h-6 mb-1" />
        <span className="text-xs">Upload</span>
      </button>
      <button
        className={`flex flex-col items-center justify-center px-4 py-2 ${currentView === 'profile' ? 'text-blue-600' : 'text-gray-500'}`}
        onClick={() => onNavigate('profile')}
      >
        <UserIcon className="w-6 h-6 mb-1" />
        <span className="text-xs">Profile</span>
      </button>
    </nav>
  );
}
