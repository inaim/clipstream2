import React from 'react';

export const VideoCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden animate-pulse">
      <div className="aspect-video bg-gray-200" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gray-200 rounded-full" />
          <div className="flex-1 space-y-2">
            <div className="h-3 bg-gray-200 rounded w-1/3" />
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="h-3 bg-gray-200 rounded w-16" />
          <div className="h-3 bg-gray-200 rounded w-16" />
          <div className="h-3 bg-gray-200 rounded w-16" />
        </div>
      </div>
    </div>
  );
};

export const FeedSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <VideoCardSkeleton key={i} />
      ))}
    </div>
  );
};

export const ProfileSkeleton: React.FC = () => {
  return (
    <div className="animate-pulse">
      <div className="flex items-center space-x-4 mb-6">
        <div className="w-24 h-24 bg-gray-200 rounded-full" />
        <div className="flex-1 space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="h-4 bg-gray-200 rounded w-2/3" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center space-y-2">
          <div className="h-6 bg-gray-200 rounded w-16 mx-auto" />
          <div className="h-4 bg-gray-200 rounded w-12 mx-auto" />
        </div>
        <div className="text-center space-y-2">
          <div className="h-6 bg-gray-200 rounded w-16 mx-auto" />
          <div className="h-4 bg-gray-200 rounded w-12 mx-auto" />
        </div>
        <div className="text-center space-y-2">
          <div className="h-6 bg-gray-200 rounded w-16 mx-auto" />
          <div className="h-4 bg-gray-200 rounded w-12 mx-auto" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="aspect-square bg-gray-200 rounded" />
        ))}
      </div>
    </div>
  );
};

export const CommentSkeleton: React.FC = () => {
  return (
    <div className="flex items-start space-x-3 animate-pulse">
      <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-1/4" />
        <div className="h-3 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-1/2" />
      </div>
    </div>
  );
};

export const SearchResultSkeleton: React.FC = () => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm animate-pulse">
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-gray-200 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-3 bg-gray-200 rounded w-1/4" />
        </div>
      </div>
    </div>
  );
};

export const DashboardStatSkeleton: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="w-12 h-12 bg-gray-200 rounded-lg" />
        <div className="h-4 bg-gray-200 rounded w-12" />
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-gray-200 rounded w-1/2" />
        <div className="h-8 bg-gray-200 rounded w-3/4" />
      </div>
    </div>
  );
};

export const ConversationSkeleton: React.FC = () => {
  return (
    <div className="p-4 flex items-start space-x-3 animate-pulse">
      <div className="w-12 h-12 bg-gray-200 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="flex items-center justify-between">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-3 bg-gray-200 rounded w-12" />
        </div>
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
    </div>
  );
};

export const MessageSkeleton: React.FC<{ align?: 'left' | 'right' }> = ({ align = 'left' }) => {
  return (
    <div className={`flex ${align === 'right' ? 'justify-end' : 'justify-start'} animate-pulse`}>
      <div
        className={`max-w-xs md:max-w-md px-4 py-2 rounded-2xl ${
          align === 'right' ? 'bg-blue-100' : 'bg-gray-200'
        }`}
      >
        <div className="h-4 bg-gray-300 rounded w-48 mb-2" />
        <div className="h-3 bg-gray-300 rounded w-16" />
      </div>
    </div>
  );
};

export const LoadingSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-16 h-16',
  };

  return (
    <div className="flex items-center justify-center">
      <div
        className={`animate-spin rounded-full border-t-2 border-b-2 border-blue-500 ${sizeClasses[size]}`}
      />
    </div>
  );
};

export const FullPageLoader: React.FC<{ message?: string }> = ({ message }) => {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-90 flex flex-col items-center justify-center z-50">
      <LoadingSpinner size="lg" />
      {message && <p className="mt-4 text-gray-600 font-medium">{message}</p>}
    </div>
  );
};

export const PullToRefreshLoader: React.FC = () => {
  return (
    <div className="flex justify-center py-4">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500" />
    </div>
  );
};

export const InfiniteScrollLoader: React.FC = () => {
  return (
    <div className="flex justify-center py-8">
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500" />
        <span className="text-sm">Loading more...</span>
      </div>
    </div>
  );
};

export const VideoGridSkeleton: React.FC<{ count?: number }> = ({ count = 12 }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="aspect-square bg-gray-200 rounded animate-pulse" />
      ))}
    </div>
  );
};

export const ShimmerEffect: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div
      className={`relative overflow-hidden bg-gray-200 ${className}`}
      style={{
        background:
          'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
      }}
    >
      <style>{`
        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
};
