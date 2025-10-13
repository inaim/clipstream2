import { useState } from 'react';
import { X, Mail, Smartphone, User as UserIcon, ArrowLeft, Globe } from 'lucide-react';
import SocialButtons from './SocialButtons';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { UsernameInput } from './UsernameInput';
import { PasswordStrength } from './PasswordStrength';
import { languages, Language } from '../../lib/i18n';

interface TikTokStyleAuthProps {
  onClose?: () => void;
}

type AuthStep = 'landing' | 'signup' | 'login' | 'phone-signup' | 'email-signup';

export function TikTokStyleAuth({ onClose }: TikTokStyleAuthProps) {
  const { signIn, signUp, signInWithSocial, sendPhoneOtp, verifyPhoneOtp } = useAuth();
  const [step, setStep] = useState<AuthStep>('landing');
  const [authMethod, setAuthMethod] = useState<'email' | 'phone'>('email');

  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState<Language>('en');
  const [ageConfirmed, setAgeConfirmed] = useState(false);

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { t } = useLanguage();

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!ageConfirmed) {
      setError(t('auth.ageVerification'));
      return;
    }

    if (!dateOfBirth) {
      setError(t('auth.dateOfBirthRequired'));
      return;
    }

    const birthDate = new Date(dateOfBirth);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (age < 13 || (age === 13 && monthDiff < 0)) {
      setError(t('auth.ageVerification'));
      return;
    }

    // Phone flow: request OTP and show code input
    if (authMethod === 'phone') {
      if (!phoneNumber) {
        setError('Please enter a valid phone number');
        return;
      }
      setLoading(true);
      try {
        if (!sendPhoneOtp) throw new Error('Phone OTP not supported');
        await sendPhoneOtp(phoneNumber);
        setOtpSent(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : t('auth.failedToSignUp'));
      } finally {
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    try {
      await signUp(email, password, username, displayName);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('auth.failedToSignUp'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpCode || !phoneNumber) {
      setError('Please enter the 6-digit code');
      return;
    }
    setVerifyingOtp(true);
    setError('');
    try {
      await (useAuth() as any).verifyPhoneOtp?.(phoneNumber, otpCode);
      // on success, close modal or navigate to landing
      setStep('landing');
      setOtpSent(false);
      setOtpCode('');
      if (onClose) onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed');
    } finally {
      setVerifyingOtp(false);
    }
  };

  // Login: send OTP for phone-based login
  const handleLoginSendOtp = async () => {
    setError('');
    if (!phoneNumber) {
      setError('Please enter a phone number');
      return;
    }
    setLoading(true);
    try {
      if (!sendPhoneOtp) throw new Error('Phone OTP not supported');
      await sendPhoneOtp(phoneNumber);
      setOtpSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginVerifyOtp = async () => {
    setError('');
    if (!otpCode) {
      setError('Please enter the code');
      return;
    }
    setVerifyingOtp(true);
    try {
      if (!verifyPhoneOtp) throw new Error('Phone OTP verification not supported');
      await verifyPhoneOtp(phoneNumber, otpCode);
      setOtpSent(false);
      setOtpCode('');
      if (onClose) onClose();
      setStep('landing');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed');
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signIn(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('auth.failedToSignIn'));
    } finally {
      setLoading(false);
    }
  };

  if (step === 'landing') {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-cyan-900 flex items-center justify-center z-50">
        {onClose && (
          <button onClick={onClose} className="absolute top-4 right-4 p-2 text-white/80 hover:text-white transition">
            <X className="w-8 h-8" />
          </button>
        )}
        <div className="w-full max-w-md mx-4">
          <div className="text-center mb-12">
            <div className="inline-block mb-4 px-4 py-2 bg-blue-500/20 backdrop-blur-sm text-blue-200 rounded-full text-sm font-semibold border border-blue-400/30">
              Next-Gen Video Platform
            </div>
            <h1 className="text-6xl font-black text-white mb-4 tracking-tight bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">ClipStream</h1>
            <p className="text-blue-200 text-lg font-medium">Create, Watch, Share with the World</p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => { setAuthMethod('email'); setStep('email-signup'); }}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-bold text-lg hover:shadow-2xl hover:scale-105 transition flex items-center justify-center gap-3 shadow-xl"
            >
              <Mail className="w-6 h-6" />
              Sign Up with Email
            </button>

            <button
              onClick={() => { setAuthMethod('phone'); setStep('signup'); }}
              className="w-full py-4 bg-white/10 backdrop-blur-sm border-2 border-white/30 text-white rounded-xl font-semibold text-lg hover:bg-white/20 transition flex items-center justify-center gap-3"
            >
              <Smartphone className="w-6 h-6" />
              Use Phone Number
            </button>

            {/* Standard Social Buttons for users who prefer social sign up */}
            <div className="mt-4">
              <SocialButtons onSocialLogin={(p) => signInWithSocial(p)} variant="large" />
            </div>
          </div>

          <div className="mt-8 text-center">
            <p className="text-blue-200 text-sm mb-2">Already have an account?</p>
            <button
              onClick={() => setStep('login')}
              className="text-white font-bold text-lg hover:text-blue-200 transition"
            >
              Log In →
            </button>
          </div>

          <div className="mt-12 text-center">
            <p className="text-blue-300/70 text-xs">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'login') {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center z-50">
        {onClose && (
          <button onClick={onClose} className="absolute top-4 right-4 p-2 text-slate-600 hover:text-slate-800 transition">
            <X className="w-7 h-7" />
          </button>
        )}

        <div className="w-full max-w-md mx-4">
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
            <div className="flex items-center mb-6">
              <button onClick={() => setStep('landing')} className="p-2 hover:bg-slate-100 rounded-full transition mr-3">
                <ArrowLeft className="w-6 h-6 text-slate-700" />
              </button>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Log In</h2>
            </div>

            <form onSubmit={handleSignIn} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                  placeholder="Enter your password"
                />
              </div>

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-bold hover:shadow-xl disabled:opacity-50 transition"
              >
                {loading ? 'Logging in...' : 'Log In'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setStep('landing')}
                  className="text-sm text-slate-600 hover:text-blue-600 transition"
                >
                  Don't have an account? <span className="font-semibold">Sign up</span>
                </button>
              </div>

              {/* Phone login: show phone input + OTP flow */}
              {authMethod === 'phone' && (
                <div className="space-y-3">
                  <label className="block text-sm font-semibold text-slate-700">Phone</label>
                  <div className="flex gap-2">
                    <input
                      type="tel"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="flex-1 px-4 py-3 border border-slate-300 rounded-xl outline-none"
                      placeholder="e.g. +15551234567"
                    />
                    {!otpSent ? (
                      <button onClick={handleLoginSendOtp} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Send code</button>
                    ) : (
                      <button onClick={handleLoginVerifyOtp} className="px-4 py-2 bg-green-600 text-white rounded-lg">Verify</button>
                    )}
                  </div>
                  {otpSent && (
                    <input
                      type="text"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      placeholder="Enter 6-digit code"
                      className="w-full px-4 py-3 border border-slate-300 rounded-xl outline-none"
                    />
                  )}
                </div>
              )}

              {/* Divider + social buttons to match signup */}
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Or continue with</span>
                </div>
              </div>

              <SocialButtons onSocialLogin={(p) => signInWithSocial(p)} variant="large" />

            </form>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'email-signup' || step === 'signup') {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col z-50 overflow-hidden">
        <div className="sticky top-0 bg-white/80 backdrop-blur-lg border-b border-slate-200 p-4 flex items-center z-10 shadow-sm">
          <button onClick={() => setStep('landing')} className="p-2 hover:bg-slate-100 rounded-full transition">
            <ArrowLeft className="w-6 h-6 text-slate-700" />
          </button>
          <h2 className="text-2xl font-bold ml-4 bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Create Account</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-6 pb-24">
          <form onSubmit={handleSignUp} className="max-w-md mx-auto space-y-6 bg-white p-8 rounded-2xl shadow-lg border border-slate-200">
            <div className="text-center mb-6">
              <div className="w-20 h-20 mx-auto bg-gradient-to-br from-blue-600 to-cyan-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
                <UserIcon className="w-10 h-10 text-white" />
              </div>
              <p className="text-slate-600 font-medium">Join ClipStream today</p>
            </div>

            {authMethod === 'phone' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone number
                </label>
                <div className="flex gap-2">
                  <select className="px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent outline-none">
                    <option>+1</option>
                    <option>+44</option>
                    <option>+91</option>
                  </select>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent outline-none"
                    placeholder="Phone number"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  We'll send you a code to verify your number
                </p>

                <div className="mt-3">
                  {!otpSent ? (
                    <button type="button" onClick={async () => {
                      try {
                        setError('');
                        setLoading(true);
                        if (!sendPhoneOtp) throw new Error('Phone OTP not supported');
                        await sendPhoneOtp(phoneNumber);
                        setOtpSent(true);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Failed to send OTP');
                      } finally {
                        setLoading(false);
                      }
                    }} className="w-full py-3 bg-blue-600 text-white rounded-lg">Send code</button>
                  ) : (
                    <div className="space-y-2">
                      <input type="text" value={otpCode} onChange={(e) => setOtpCode(e.target.value)} placeholder="Enter code" className="w-full px-4 py-3 border border-gray-300 rounded-lg" />
                      <button type="button" onClick={handleVerifyOtp} className="w-full py-3 bg-green-600 text-white rounded-lg">Verify code</button>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none"
                placeholder="Email address"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <UsernameInput
                value={username}
                onChange={setUsername}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date of birth
              </label>
              <input
                type="date"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
                required
                max={new Date(Date.now() - 13 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                You must be 13 or older to use ClipStream
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Globe className="w-4 h-4 inline mr-1" />
                Preferred Language
              </label>
              <div className="relative">
                <select
                  value={preferredLanguage}
                  onChange={(e) => setPreferredLanguage(e.target.value as Language)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none appearance-none bg-white"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.nativeName} ({lang.name})
                    </option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                  <span className="text-lg">
                    {languages.find(l => l.code === preferredLanguage)?.flag}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                We'll show you content in this language
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-blue focus:border-transparent outline-none"
                placeholder="Create a strong password"
              />
              <PasswordStrength password={password} />
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ageConfirmed}
                  onChange={(e) => setAgeConfirmed(e.target.checked)}
                  required
                  className="mt-1 w-5 h-5 text-sky-blue border-gray-300 rounded focus:ring-sky-blue"
                />
                <span className="text-sm text-gray-700">
                  I confirm that I am <strong>13 years or older</strong> and agree to the Terms of Service and Privacy Policy
                </span>
              </label>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-sky-blue text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 transition"
            >
              {loading ? 'Creating account...' : 'Sign up'}
            </button>

            <p className="text-xs text-gray-500 text-center">
              By signing up, you agree to our Terms of Service and Privacy Policy
            </p>
          </form>
        </div>
      </div>
    );
  }

  return null;
}
