import { Globe, ChevronDown, Check } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { languages, Language } from '../../lib/i18n';
import { useState, useRef, useEffect } from 'react';

interface TikTokLanguageSelectorProps {
  variant?: 'header' | 'mobile' | 'floating';
  showText?: boolean;
}

export function TikTokLanguageSelector({ 
  variant = 'header', 
  showText = true 
}: TikTokLanguageSelectorProps) {
  const { language, setLanguage, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find(l => l.code === language);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const getButtonStyles = () => {
    switch (variant) {
      case 'mobile':
        return 'flex items-center gap-2 p-3 rounded-xl bg-gray-100 hover:bg-gray-200 transition-all duration-200 active:scale-95';
      case 'floating':
        return 'flex items-center gap-2 px-4 py-3 bg-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200';
      default:
        return 'flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-all duration-200';
    }
  };

  const getDropdownStyles = () => {
    switch (variant) {
      case 'mobile':
        return 'absolute bottom-full left-0 mb-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 py-3 z-50 max-h-96 overflow-y-auto';
      case 'floating':
        return 'absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 py-3 z-50 max-h-96 overflow-y-auto';
      default:
        return 'absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 py-3 z-50 max-h-96 overflow-y-auto';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={getButtonStyles()}
        title={t('nav.language')}
      >
        <div className="flex items-center gap-2">
          <span className="text-xl">{currentLanguage?.flag}</span>
          <Globe className="w-4 h-4 text-gray-600" />
        </div>
        {showText && (
          <span className="text-sm font-medium text-gray-700 hidden sm:inline">
            {currentLanguage?.nativeName}
          </span>
        )}
        <ChevronDown 
          className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {isOpen && (
        <div className={getDropdownStyles()}>
          <div className="px-4 py-2 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              {t('nav.language')}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {t('common.chooseLanguage')}
            </p>
          </div>
          
          <div className="py-2">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  setLanguage(lang.code as Language);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-all duration-200 flex items-center gap-3 group ${
                  language === lang.code 
                    ? 'bg-blue-50 border-r-4 border-blue-500' 
                    : 'hover:border-r-4 hover:border-transparent'
                }`}
              >
                <span className="text-2xl transition-transform group-hover:scale-110">
                  {lang.flag}
                </span>
                <div className="flex-1">
                  <div className={`font-medium transition-colors ${
                    language === lang.code ? 'text-blue-700' : 'text-gray-900'
                  }`}>
                    {lang.nativeName}
                  </div>
                  <div className="text-xs text-gray-500">{lang.name}</div>
                </div>
                {language === lang.code && (
                  <Check className="w-5 h-5 text-blue-500" />
                )}
              </button>
            ))}
          </div>
          
          <div className="px-4 py-2 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center">
              More languages coming soon
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
