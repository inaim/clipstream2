export type Profile = {
  id?: string;
  user_id?: string;
  email?: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string | null;
};

export type Video = {
  id?: string;
  title?: string;
  description?: string;
  owner_id?: string;
  playback_url?: string;
  thumbnail_url?: string;
  views?: number;
  likes_count?: number;
};
