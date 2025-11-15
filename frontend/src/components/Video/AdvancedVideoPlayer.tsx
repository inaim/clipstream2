import React, { useRef, useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Settings,
  SkipForward,
  SkipBack,
} from 'lucide-react';

interface AdvancedVideoPlayerProps {
  src: string;
  poster?: string;
  autoPlay?: boolean;
  loop?: boolean;
  muted?: boolean;
  className?: string;
  onEnded?: () => void;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  showControls?: boolean;
  playbackRates?: number[];
}

export const AdvancedVideoPlayer: React.FC<AdvancedVideoPlayerProps> = ({
  src,
  poster,
  autoPlay = false,
  loop = false,
  muted = false,
  className = '',
  onEnded,
  onTimeUpdate,
  showControls = true,
  playbackRates = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [isMuted, setIsMuted] = useState(muted);
  const [volume, setVolume] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffered, setBuffered] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [quality, setQuality] = useState('auto');
  const [showControlsOverlay, setShowControlsOverlay] = useState(true);
  const hideControlsTimeoutRef = useRef<NodeJS.Timeout>();

  // Auto-hide controls
  useEffect(() => {
    if (showControlsOverlay && isPlaying) {
      hideControlsTimeoutRef.current = setTimeout(() => {
        setShowControlsOverlay(false);
      }, 3000);
    }
    return () => {
      if (hideControlsTimeoutRef.current) {
        clearTimeout(hideControlsTimeoutRef.current);
      }
    };
  }, [showControlsOverlay, isPlaying]);

  const handleMouseMove = () => {
    setShowControlsOverlay(true);
    if (hideControlsTimeoutRef.current) {
      clearTimeout(hideControlsTimeoutRef.current);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      if (newVolume === 0) {
        setIsMuted(true);
      } else if (isMuted) {
        setIsMuted(false);
        videoRef.current.muted = false;
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      if (onTimeUpdate) {
        onTimeUpdate(videoRef.current.currentTime, videoRef.current.duration);
      }
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleProgress = () => {
    if (videoRef.current && videoRef.current.buffered.length > 0) {
      const bufferedEnd = videoRef.current.buffered.end(
        videoRef.current.buffered.length - 1
      );
      const duration = videoRef.current.duration;
      if (duration > 0) {
        setBuffered((bufferedEnd / duration) * 100);
      }
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const changePlaybackRate = (rate: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
      setShowSettings(false);
    }
  };

  const skip = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(
        0,
        Math.min(videoRef.current.duration, videoRef.current.currentTime + seconds)
      );
    }
  };

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className={`relative bg-black ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setShowControlsOverlay(false)}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        loop={loop}
        muted={muted}
        playsInline
        className="w-full h-full object-contain"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onProgress={handleProgress}
        onEnded={() => {
          setIsPlaying(false);
          onEnded?.();
        }}
        onClick={togglePlay}
      />

      {/* Loading Overlay */}
      {!duration && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-white"></div>
        </div>
      )}

      {/* Controls Overlay */}
      {showControls && (
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent transition-opacity duration-300 ${
            showControlsOverlay ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {/* Center Play/Pause Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={togglePlay}
              className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-all"
            >
              {isPlaying ? (
                <Pause className="w-8 h-8 text-white" />
              ) : (
                <Play className="w-8 h-8 text-white ml-1" />
              )}
            </button>
          </div>

          {/* Bottom Controls */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            {/* Progress Bar */}
            <div className="mb-3">
              <div className="relative">
                {/* Buffered Progress */}
                <div className="absolute h-1 bg-white/30 rounded-full" style={{ width: `${buffered}%` }} />
                {/* Current Progress */}
                <div
                  className="absolute h-1 bg-blue-500 rounded-full"
                  style={{ width: `${progressPercentage}%` }}
                />
                {/* Seek Bar */}
                <input
                  type="range"
                  min="0"
                  max={duration || 0}
                  value={currentTime}
                  onChange={handleSeek}
                  className="w-full h-1 bg-white/10 rounded-full appearance-none cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                    [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500
                    [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-lg
                    [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full
                    [&::-moz-range-thumb]:bg-blue-500 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {/* Play/Pause */}
                <button onClick={togglePlay} className="text-white hover:text-blue-400 transition">
                  {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                </button>

                {/* Skip Backward */}
                <button
                  onClick={() => skip(-10)}
                  className="text-white hover:text-blue-400 transition"
                  title="Skip backward 10s"
                >
                  <SkipBack className="w-5 h-5" />
                </button>

                {/* Skip Forward */}
                <button
                  onClick={() => skip(10)}
                  className="text-white hover:text-blue-400 transition"
                  title="Skip forward 10s"
                >
                  <SkipForward className="w-5 h-5" />
                </button>

                {/* Volume */}
                <div className="flex items-center space-x-2 group">
                  <button onClick={toggleMute} className="text-white hover:text-blue-400 transition">
                    {isMuted || volume === 0 ? (
                      <VolumeX className="w-6 h-6" />
                    ) : (
                      <Volume2 className="w-6 h-6" />
                    )}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="w-0 group-hover:w-20 transition-all duration-300 h-1 bg-white/10 rounded-full appearance-none cursor-pointer
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3
                      [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white
                      [&::-webkit-slider-thumb]:cursor-pointer
                      [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:rounded-full
                      [&::-moz-range-thumb]:bg-white [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0"
                  />
                </div>

                {/* Time Display */}
                <div className="text-white text-sm font-medium">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {/* Settings (Playback Speed) */}
                <div className="relative">
                  <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="text-white hover:text-blue-400 transition"
                  >
                    <Settings className="w-6 h-6" />
                  </button>
                  {showSettings && (
                    <div className="absolute bottom-full right-0 mb-2 bg-gray-900 rounded-lg p-2 shadow-xl min-w-[120px]">
                      <div className="text-white text-xs font-semibold mb-2 px-2">Playback Speed</div>
                      {playbackRates.map((rate) => (
                        <button
                          key={rate}
                          onClick={() => changePlaybackRate(rate)}
                          className={`w-full text-left px-3 py-1.5 text-sm rounded transition ${
                            playbackRate === rate
                              ? 'bg-blue-500 text-white'
                              : 'text-gray-300 hover:bg-gray-800'
                          }`}
                        >
                          {rate}x
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Fullscreen */}
                <button
                  onClick={toggleFullscreen}
                  className="text-white hover:text-blue-400 transition"
                >
                  {isFullscreen ? <Minimize className="w-6 h-6" /> : <Maximize className="w-6 h-6" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
