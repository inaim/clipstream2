import { Home, Search, PlusSquare, MessageSquare, User } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface MobileNavigationProps {
  currentTab: 'home' | 'search' | 'upload' | 'inbox' | 'profile';
  onTabChange: (tab: 'home' | 'search' | 'upload' | 'inbox' | 'profile') => void;
  inboxUnread?: number;
}

export function MobileNavigation({ currentTab, onTabChange, inboxUnread = 0 }: MobileNavigationProps) {
  const { t } = useLanguage();

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-black border-t border-gray-800 z-50">
      <div className="flex items-center justify-around h-16 px-2">
        <button
          onClick={() => onTabChange('home')}
          className="flex flex-col items-center justify-center flex-1 h-full active:scale-95 transition"
        >
          <Home
            className={`w-7 h-7 mb-1 transition ${
              currentTab === 'home' ? 'text-white' : 'text-gray-400'
            }`}
          />
          <span
            className={`text-xs transition ${
              currentTab === 'home' ? 'text-white' : 'text-gray-400'
            }`}
          >
            {t('nav.home')}
          </span>
        </button>

        <button
          onClick={() => onTabChange('search')}
          className="flex flex-col items-center justify-center flex-1 h-full active:scale-95 transition"
        >
          <Search
            className={`w-7 h-7 mb-1 transition ${
              currentTab === 'search' ? 'text-white' : 'text-gray-400'
            }`}
          />
          <span
            className={`text-xs transition ${
              currentTab === 'search' ? 'text-white' : 'text-gray-400'
            }`}
          >
            {t('nav.discover')}
          </span>
        </button>

        <button
          onClick={() => onTabChange('upload')}
          className="flex flex-col items-center justify-center flex-1 h-full active:scale-90 transition"
        >
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg blur-sm"></div>
            <div className="relative bg-black rounded-lg p-1">
              <PlusSquare className="w-6 h-6 text-white" />
            </div>
          </div>
        </button>

        <button
          onClick={() => onTabChange('inbox')}
          className="flex flex-col items-center justify-center flex-1 h-full active:scale-95 transition relative"
        >
          <MessageSquare
            className={`w-7 h-7 mb-1 transition ${
              currentTab === 'inbox' ? 'text-white' : 'text-gray-400'
            }`}
          />
          <span
            className={`text-xs transition ${
              currentTab === 'inbox' ? 'text-white' : 'text-gray-400'
            }`}
          >
            {t('nav.inbox')}
          </span>

          {/* inbox badge */}
          {inboxUnread > 0 && (
            <span className="absolute -top-1 right-6 min-w-[1rem] h-4 bg-red-500 rounded-full flex items-center justify-center text-xs text-white font-semibold px-1">
              {inboxUnread > 9 ? '9+' : inboxUnread}
            </span>
          )}
        </button>

        <button
          onClick={() => onTabChange('profile')}
          className="flex flex-col items-center justify-center flex-1 h-full active:scale-95 transition"
        >
          <User
            className={`w-7 h-7 mb-1 transition ${
              currentTab === 'profile' ? 'text-white' : 'text-gray-400'
            }`}
          />
          <span
            className={`text-xs transition ${
              currentTab === 'profile' ? 'text-white' : 'text-gray-400'
            }`}
          >
            {t('nav.profile')}
          </span>
        </button>
      </div>
    </div>
  );
}
