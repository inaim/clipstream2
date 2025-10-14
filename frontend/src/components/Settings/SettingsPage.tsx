import { useState } from 'react';
import {
  User,
  Lock,
  Bell,
  Shield,
  Eye,
  Globe,
  HelpCircle,
  FileText,
  Info,
  ChevronRight,
  LogOut,
  Moon,
  Sun,
  Smartphone,
  Download,
  Trash2,
  UserX,
  AlertTriangle,
  Check,
  X,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface SettingsPageProps {
  onClose: () => void;
}

export function SettingsPage({ onClose }: SettingsPageProps) {
  const { profile, signOut } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    likes: true,
    comments: true,
    newFollowers: true,
    mentions: true,
    liveStreams: false,
    videoUpdates: true,
  });
  const [privacy, setPrivacy] = useState({
    privateAccount: false,
    allowComments: true,
    allowDuet: true,
    allowStitch: true,
    allowDownload: true,
    suggestAccount: true,
  });

  const handleLogout = async () => {
    if (confirm(t('settings.confirmLogout') || 'Are you sure you want to log out?')) {
      await signOut();
      onClose();
    }
  };

  const settingsSections = [
    {
      id: 'account',
      title: t('settings.accountAndProfile') || 'Account and Profile',
      icon: User,
      items: [
        { label: t('settings.manageAccount') || 'Manage account', action: () => setActiveSection('manage-account') },
        { label: t('settings.changePassword') || 'Change password', action: () => setActiveSection('change-password') },
        { label: t('settings.phoneNumber') || 'Phone number', action: () => setActiveSection('phone') },
        { label: t('settings.emailAddress') || 'Email address', action: () => setActiveSection('email') },
      ],
    },
    {
      id: 'privacy',
      title: t('settings.privacyAndSafety') || 'Privacy and Safety',
      icon: Shield,
      items: [
        { label: t('settings.privacy') || 'Privacy', action: () => setActiveSection('privacy') },
        { label: t('settings.blockedAccounts') || 'Blocked accounts', action: () => setActiveSection('blocked') },
        { label: t('settings.mutedAccounts') || 'Muted accounts', action: () => setActiveSection('muted') },
        { label: t('settings.downloadData') || 'Download your data', action: () => setActiveSection('download-data') },
      ],
    },
    {
      id: 'notifications',
      title: t('settings.notifications') || 'Notifications',
      icon: Bell,
      items: [
        { label: t('settings.pushNotifications') || 'Push notifications', action: () => setActiveSection('notifications') },
        { label: t('settings.emailNotifications') || 'Email notifications', action: () => setActiveSection('email-notifications') },
      ],
    },
    {
      id: 'content',
      title: t('settings.contentPreferences') || 'Content Preferences',
      icon: Eye,
      items: [
        { label: t('settings.language') || 'Language', action: () => setActiveSection('language') },
        { label: t('settings.contentLanguage') || 'Content language', action: () => setActiveSection('content-language') },
        { label: t('settings.darkMode') || 'Dark mode', action: () => setActiveSection('dark-mode') },
      ],
    },
    {
      id: 'support',
      title: t('settings.supportAndAbout') || 'Support and About',
      icon: HelpCircle,
      items: [
        { label: t('settings.reportProblem') || 'Report a problem', action: () => setActiveSection('report') },
        { label: t('settings.helpCenter') || 'Help Center', action: () => window.open('https://support.clipstream.app', '_blank') },
        { label: t('settings.termsOfService') || 'Terms of Service', action: () => setActiveSection('terms') },
        { label: t('settings.privacyPolicy') || 'Privacy Policy', action: () => setActiveSection('privacy-policy') },
        { label: t('settings.aboutClipStream') || 'About ClipStream', action: () => setActiveSection('about') },
      ],
    },
  ];

  const renderMainSettings = () => (
    <div className="space-y-6">
      {settingsSections.map((section) => (
        <div key={section.id} className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
            <section.icon className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-800">{section.title}</h3>
          </div>
          <div className="divide-y divide-gray-100">
            {section.items.map((item, idx) => (
              <button
                key={idx}
                onClick={item.action}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition active:bg-gray-100"
              >
                <span className="text-gray-700">{item.label}</span>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <button
          onClick={handleLogout}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-red-50 transition active:bg-red-100 text-red-600"
        >
          <div className="flex items-center gap-3">
            <LogOut className="w-5 h-5" />
            <span className="font-medium">{t('common.signOut') || 'Log out'}</span>
          </div>
        </button>
      </div>

      <div className="text-center text-sm text-gray-500 py-4">
        <p>ClipStream v1.0.0</p>
        <p className="mt-1">© 2025 ClipStream. All rights reserved.</p>
      </div>
    </div>
  );

  const renderPrivacySettings = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-800 mb-4">{t('settings.privacySettings') || 'Privacy Settings'}</h2>
      
      <div className="bg-white rounded-lg shadow-sm divide-y divide-gray-100">
        <div className="px-4 py-3 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">{t('settings.privateAccount') || 'Private account'}</p>
            <p className="text-sm text-gray-500">{t('settings.privateAccountDesc') || 'Only approved followers can see your videos'}</p>
          </div>
          <button
            onClick={() => setPrivacy({ ...privacy, privateAccount: !privacy.privateAccount })}
            className={`w-12 h-6 rounded-full transition ${privacy.privateAccount ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${privacy.privateAccount ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="px-4 py-3 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">{t('settings.allowComments') || 'Allow comments'}</p>
            <p className="text-sm text-gray-500">{t('settings.allowCommentsDesc') || 'Let people comment on your videos'}</p>
          </div>
          <button
            onClick={() => setPrivacy({ ...privacy, allowComments: !privacy.allowComments })}
            className={`w-12 h-6 rounded-full transition ${privacy.allowComments ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${privacy.allowComments ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="px-4 py-3 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">{t('settings.allowDuet') || 'Allow Duet'}</p>
            <p className="text-sm text-gray-500">{t('settings.allowDuetDesc') || 'Let others create Duets with your videos'}</p>
          </div>
          <button
            onClick={() => setPrivacy({ ...privacy, allowDuet: !privacy.allowDuet })}
            className={`w-12 h-6 rounded-full transition ${privacy.allowDuet ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${privacy.allowDuet ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="px-4 py-3 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">{t('settings.allowDownload') || 'Allow downloads'}</p>
            <p className="text-sm text-gray-500">{t('settings.allowDownloadDesc') || 'Let others download your videos'}</p>
          </div>
          <button
            onClick={() => setPrivacy({ ...privacy, allowDownload: !privacy.allowDownload })}
            className={`w-12 h-6 rounded-full transition ${privacy.allowDownload ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${privacy.allowDownload ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>

        <div className="px-4 py-3 flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">{t('settings.suggestAccount') || 'Suggest your account to others'}</p>
            <p className="text-sm text-gray-500">{t('settings.suggestAccountDesc') || 'Allow ClipStream to suggest your account'}</p>
          </div>
          <button
            onClick={() => setPrivacy({ ...privacy, suggestAccount: !privacy.suggestAccount })}
            className={`w-12 h-6 rounded-full transition ${privacy.suggestAccount ? 'bg-blue-600' : 'bg-gray-300'}`}
          >
            <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${privacy.suggestAccount ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-800 mb-4">{t('settings.notificationSettings') || 'Notification Settings'}</h2>
      
      <div className="bg-white rounded-lg shadow-sm divide-y divide-gray-100">
        {Object.entries(notifications).map(([key, value]) => (
          <div key={key} className="px-4 py-3 flex items-center justify-between">
            <p className="font-medium text-gray-800 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
            <button
              onClick={() => setNotifications({ ...notifications, [key]: !value })}
              className={`w-12 h-6 rounded-full transition ${value ? 'bg-blue-600' : 'bg-gray-300'}`}
            >
              <div className={`w-5 h-5 bg-white rounded-full shadow transform transition ${value ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-50 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">
            {activeSection ? (
              <button onClick={() => setActiveSection(null)} className="flex items-center gap-2 text-blue-600 hover:text-blue-700">
                <ChevronRight className="w-6 h-6 rotate-180" />
                <span>{t('common.back') || 'Back'}</span>
              </button>
            ) : (
              t('settings.title') || 'Settings'
            )}
          </h1>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!activeSection && renderMainSettings()}
          {activeSection === 'privacy' && renderPrivacySettings()}
          {activeSection === 'notifications' && renderNotificationSettings()}
          {activeSection && !['privacy', 'notifications'].includes(activeSection) && (
            <div className="text-center py-12">
              <p className="text-gray-500">{t('settings.comingSoon') || 'This feature is coming soon!'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

