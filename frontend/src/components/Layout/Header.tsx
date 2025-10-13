import { Video, Home, User as UserIcon, Upload, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { TikTokLanguageSelector } from './TikTokLanguageSelector';

interface HeaderProps {
  currentView: 'feed' | 'profile';
  onNavigate: (view: 'feed' | 'profile') => void;
  onUploadClick: () => void;
}

export function Header({ currentView, onNavigate, onUploadClick }: HeaderProps) {
  const { profile, signOut } = useAuth();
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => onNavigate('feed')}>
            <Video className="w-8 h-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">ClipStream</span>
          </div>

          <nav className="flex items-center gap-2">
            <button
              onClick={() => onNavigate('feed')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                currentView === 'feed'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Home className="w-5 h-5" />
              <span className="hidden sm:inline">{t('nav.home')}</span>
            </button>

            <button
              onClick={onUploadClick}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
            >
              <Upload className="w-5 h-5" />
              <span className="hidden sm:inline">{t('nav.upload')}</span>
            </button>

            <button
              onClick={() => onNavigate('profile')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                currentView === 'profile'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <UserIcon className="w-5 h-5" />
              <span className="hidden sm:inline">{profile?.username}</span>
            </button>

            <TikTokLanguageSelector variant="header" />

            <button
              onClick={signOut}
              className="p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
              title={t('common.signOut')}
            >
              <LogOut className="w-5 h-5" />
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
