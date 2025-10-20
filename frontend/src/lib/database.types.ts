export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          username: string;
          display_name: string;
          bio: string;
          avatar_url: string;
          location: string;
          latitude: number | null;
          longitude: number | null;
          phone_number: string;
          followers_count: number;
          following_count: number;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          username: string;
          display_name: string;
          bio?: string;
          avatar_url?: string;
          location?: string;
          latitude?: number | null;
          longitude?: number | null;
          phone_number?: string;
          followers_count?: number;
          following_count?: number;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          username?: string;
          display_name?: string;
          bio?: string;
          avatar_url?: string;
          location?: string;
          latitude?: number | null;
          longitude?: number | null;
          phone_number?: string;
          followers_count?: number;
          following_count?: number;
          created_at?: string;
          updated_at?: string;
        };
      };
      videos: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          description: string;
          video_url: string;
          thumbnail_url: string;
          duration: number;
          views_count: number;
          likes_count: number;
          comments_count: number;
          shares_count: number;
          latitude: number | null;
          longitude: number | null;
          location_name: string;
          hashtags: string[];
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          description?: string;
          video_url: string;
          thumbnail_url?: string;
          duration?: number;
          views_count?: number;
          likes_count?: number;
          comments_count?: number;
          shares_count?: number;
          latitude?: number | null;
          longitude?: number | null;
          location_name?: string;
          hashtags?: string[];
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          description?: string;
          video_url?: string;
          thumbnail_url?: string;
          duration?: number;
          views_count?: number;
          likes_count?: number;
          comments_count?: number;
          shares_count?: number;
          latitude?: number | null;
          longitude?: number | null;
          location_name?: string;
          hashtags?: string[];
          created_at?: string;
          updated_at?: string;
        };
      };
      likes: {
        Row: {
          id: string;
          user_id: string;
          video_id: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          video_id: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          video_id?: string;
          created_at?: string;
        };
      };
      comments: {
        Row: {
          id: string;
          user_id: string;
          video_id: string;
          content: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          video_id: string;
          content: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          video_id?: string;
          content?: string;
          created_at?: string;
          updated_at?: string;
        };
      };
      follows: {
        Row: {
          id: string;
          follower_id: string;
          following_id: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          follower_id: string;
          following_id: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          follower_id?: string;
          following_id?: string;
          created_at?: string;
        };
      };
    };
  };
}
