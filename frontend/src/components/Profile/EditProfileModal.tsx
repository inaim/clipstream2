import { useState, useRef } from 'react';
import { X, Camera, Upload, User } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../lib/surrealdb';
import { useLanguage } from '../../contexts/LanguageContext';

import type { Profile } from '../../lib/types';

interface EditProfileModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function EditProfileModal({ onClose, onSuccess }: EditProfileModalProps) {
  const { user, profile } = useAuth();
  const { t } = useLanguage();
  const [displayName, setDisplayName] = useState(profile?.display_name || '');
  const [bio, setBio] = useState((profile as Profile | null)?.bio || '');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>((profile as Profile | null)?.avatar_url || null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Avatar must be less than 5MB');
        return;
      }
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      setAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setUploading(true);
    setError('');

    try {
  let avatarUrl = (profile as Profile | null)?.avatar_url;

      if (avatarFile) {
        const fileExt = avatarFile.name.split('.').pop();
        const fileName = `${Date.now()}.${fileExt}`;
  const filePath = `${(user.id || user.user_id)}/${fileName}`;

        const { error: uploadError } = await supabase.storage
          .from('avatars')
          .upload(filePath, avatarFile);

        if (uploadError) {
          if (uploadError.message.includes('Bucket not found')) {
            const { error: bucketError } = await supabase.storage.createBucket('avatars', {
              public: true,
            });

            if (!bucketError) {
              const { error: retryError } = await supabase.storage
                .from('avatars')
                .upload(filePath, avatarFile);

              if (retryError) throw retryError;
            } else {
              throw uploadError;
            }
          } else {
            throw uploadError;
          }
        }

        const { data: { publicUrl } } = supabase.storage
          .from('avatars')
          .getPublicUrl(filePath);

        avatarUrl = publicUrl;
      }

      const { error: updateError } = await supabase
        .from('profiles')
        .update({
          display_name: displayName,
          bio: bio,
          avatar_url: avatarUrl,
        })
        .eq('id', user.id || user.user_id);

      if (updateError) throw updateError;

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">{t('profile.edit')}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-full transition active:scale-95"
          >
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="flex flex-col items-center">
            <div className="relative">
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center overflow-hidden">
                {avatarPreview ? (
                  <img
                    src={avatarPreview}
                    alt="Avatar preview"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-16 h-16 text-white" />
                )}
              </div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 p-3 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full shadow-lg hover:shadow-xl transition active:scale-95"
              >
                <Camera className="w-5 h-5 text-white" />
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              className="hidden"
            />
            <p className="text-sm text-gray-400 mt-3">
              Click camera icon to upload new avatar
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Display Name
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder={t('profile.displayNamePlaceholder')}
              className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition"
              maxLength={50}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Bio
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder={t('profile.bioPlaceholder')}
              rows={4}
              className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition resize-none"
              maxLength={200}
            />
            <p className="text-xs text-gray-400 mt-1">
              {bio.length}/200 characters
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 bg-gray-800 text-white rounded-lg font-semibold hover:bg-gray-700 transition active:scale-95"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {uploading ? t('common.loading') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
