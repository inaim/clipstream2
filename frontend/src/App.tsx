import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { LandingPage } from './components/Landing/LandingPage';
import { TikTokStyleAuth } from './components/Auth/TikTokStyleAuth';
import { EnhancedMainApp } from './components/Layout/EnhancedMainApp';
import { AuthCallback } from './components/Auth/AuthCallback';

function AppContent() {
  const { user, loading } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [isOAuthCallback, setIsOAuthCallback] = useState(false);

  useEffect(() => {
    // Check if this is an OAuth callback URL
    const urlParams = new URLSearchParams(window.location.search);
    const hasToken = urlParams.has('token');
    const hasUserId = urlParams.has('user_id');
    
    if (hasToken && hasUserId) {
      setIsOAuthCallback(true);
    }
  }, []);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 to-blue-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-white">Loading ClipStream...</p>
        </div>
      </div>
    );
  }

  // Handle OAuth callback
  if (isOAuthCallback) {
    return (
      <AuthCallback
        onSuccess={() => {
          setIsOAuthCallback(false);
          // Clear URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);
          // Show main app after successful auth (no reload)
        }}
        onError={() => {
          setIsOAuthCallback(false);
          setShowAuth(true);
          // Clear URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);
        }}
      />
    );
  }

  if (user) {
    return <EnhancedMainApp />;
  }

  if (showAuth) {
    return <TikTokStyleAuth onClose={() => setShowAuth(false)} />;
  }

  return <LandingPage onGetStarted={() => setShowAuth(true)} />;
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
