import React from 'react';
import { FcGoogle } from 'react-icons/fc';
import { FaFacebook, FaApple } from 'react-icons/fa';

interface SocialButtonsProps {
  onSocialLogin: (provider: string) => void;
  socialLoading?: string | null;
  variant?: 'large' | 'compact';
}

export default function SocialButtons({ onSocialLogin, socialLoading, variant = 'large' }: SocialButtonsProps) {
  const containerClasses = variant === 'large' ? 'w-full flex flex-col gap-3 mt-2' : 'w-full flex flex-col gap-2 mt-1';
  const btnPadding = variant === 'large' ? 'py-3 text-base' : 'py-2 text-sm';

  return (
    <div className={containerClasses}>
      <button
        type="button"
        onClick={() => onSocialLogin('google')}
        disabled={!!socialLoading}
        className={`w-full flex items-center justify-center gap-3 ${btnPadding} bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 transition font-semibold text-gray-800 disabled:opacity-50`}
      >
        <FcGoogle className="w-6 h-6" />
        Continue with Google
      </button>
      <button
        type="button"
        onClick={() => onSocialLogin('facebook')}
        disabled={!!socialLoading}
        className={`w-full flex items-center justify-center gap-3 ${btnPadding} bg-blue-600 rounded-lg shadow-sm hover:bg-blue-700 transition font-semibold text-white disabled:opacity-50`}
      >
        <FaFacebook className="w-6 h-6" />
        Continue with Facebook
      </button>
      <button
        type="button"
        onClick={() => onSocialLogin('apple')}
        disabled={!!socialLoading}
        className={`w-full flex items-center justify-center gap-3 ${btnPadding} bg-black rounded-lg shadow-sm hover:bg-gray-900 transition font-semibold text-white disabled:opacity-50`}
      >
        <FaApple className="w-6 h-6" />
        Continue with Apple
      </button>
    </div>
  );
}
