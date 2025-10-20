import { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const { t } = useLanguage();

  useEffect(() => {
    // Check if already installed
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches;
    if (isInstalled) {
      return;
    }

    // Check if user has dismissed the prompt before
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      return;
    }

    // Listen for the beforeinstallprompt event
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      
      // Show prompt after 30 seconds
      setTimeout(() => {
        setShowPrompt(true);
      }, 30000);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) {
      // For iOS, show instructions
      if (isIOS()) {
        alert(
          'To install ClipStream:\n\n' +
          '1. Tap the Share button (square with arrow)\n' +
          '2. Scroll down and tap "Add to Home Screen"\n' +
          '3. Tap "Add" in the top right'
        );
      }
      return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
    }

    // Clear the deferredPrompt
    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  const isIOS = () => {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;
  };

  if (!showPrompt && !isIOS()) {
    return null;
  }

  // Show iOS-specific prompt
  if (isIOS() && showPrompt) {
    return (
      <div className="fixed bottom-20 left-4 right-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg shadow-2xl p-4 z-50 animate-slide-up">
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 p-1 hover:bg-white/20 rounded-full transition"
        >
          <X className="w-4 h-4" />
        </button>
        
        <div className="flex items-start gap-3">
          <div className="bg-white/20 p-2 rounded-lg">
            <Download className="w-6 h-6" />
          </div>
          
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-1">Install ClipStream</h3>
            <p className="text-sm text-white/90 mb-3">
              Add to your home screen for the best experience!
            </p>
            
            <div className="text-xs text-white/80 space-y-1">
              <p>📱 Tap the Share button below</p>
              <p>➕ Select "Add to Home Screen"</p>
              <p>✅ Tap "Add"</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show Android/Chrome prompt
  return (
    <div className="fixed bottom-20 left-4 right-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg shadow-2xl p-4 z-50 animate-slide-up">
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 p-1 hover:bg-white/20 rounded-full transition"
      >
        <X className="w-4 h-4" />
      </button>
      
      <div className="flex items-center gap-3 mb-3">
        <div className="bg-white/20 p-2 rounded-lg">
          <Download className="w-6 h-6" />
        </div>
        
        <div className="flex-1">
          <h3 className="font-bold text-lg">Install ClipStream</h3>
          <p className="text-sm text-white/90">
            Get the app experience on your device!
          </p>
        </div>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={handleInstall}
          className="flex-1 bg-white text-blue-600 font-semibold py-2 px-4 rounded-lg hover:bg-blue-50 transition active:scale-95"
        >
          Install
        </button>
        <button
          onClick={handleDismiss}
          className="px-4 py-2 text-white/90 hover:bg-white/10 rounded-lg transition active:scale-95"
        >
          Not now
        </button>
      </div>
    </div>
  );
}

