import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

interface AuthCallbackProps {
  onSuccess: () => void;
  onError: () => void;
}

export function AuthCallback({ onSuccess, onError }: AuthCallbackProps) {
  const { user } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Parse URL parameters manually
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const userId = urlParams.get('user_id');
        const provider = urlParams.get('provider');
        const error = urlParams.get('error');

        if (error) {
          throw new Error(error);
        }

        if (!token || !userId) {
          throw new Error('Missing authentication data');
        }

        // Store the authentication data
        localStorage.setItem('clipstream_token', token);
        localStorage.setItem('clipstream_user_id', userId);

        setStatus('success');
        setMessage(`Successfully signed in with ${provider || 'social account'}!`);

        // Redirect to dashboard immediately
        setTimeout(() => {
          onSuccess();
        }, 1000);

      } catch (err) {
        console.error('Authentication error:', err);
        setStatus('error');
        setMessage(err instanceof Error ? err.message : 'Authentication failed');

        // Redirect to login page after error
        setTimeout(() => {
          onError();
        }, 3000);
      }
    };

    // Only process if we're not already logged in
    if (!user) {
      handleCallback();
    } else {
      // User is already logged in, redirect to main app
      onSuccess();
    }
  }, [user, onSuccess, onError]);

  const getIcon = () => {
    switch (status) {
      case 'loading':
        return <Loader2 className="w-16 h-16 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-16 h-16 text-green-500" />;
      case 'error':
        return <XCircle className="w-16 h-16 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'loading':
        return 'text-blue-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-500 to-red-500 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          {getIcon()}
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          {status === 'loading' && 'Processing...'}
          {status === 'success' && 'Welcome to ClipStream!'}
          {status === 'error' && 'Authentication Failed'}
        </h1>
        
        <p className={`text-lg ${getStatusColor()} mb-6`}>
          {message}
        </p>

        {status === 'loading' && (
          <div className="text-sm text-gray-500">
            Please wait while we complete your sign-in...
          </div>
        )}

        {status === 'success' && (
          <div className="text-sm text-gray-500">
            Redirecting you to the app...
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-3">
            <div className="text-sm text-gray-500">
              Redirecting you back to sign in...
            </div>
            <button
              onClick={onError}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Go to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}