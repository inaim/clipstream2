import React, { useState, useRef, useEffect } from 'react';
import {
  Scissors,
  Type,
  Sparkles,
  Music,
  Palette,
  Wand2,
  Smile,
  Download,
  Upload,
  RotateCcw,
  Check,
  X,
  Volume2,
  VolumeX,
  Play,
  Pause,
} from 'lucide-react';

interface Filter {
  id: string;
  name: string;
  cssFilter: string;
}

interface Sticker {
  id: string;
  emoji: string;
  name: string;
}

interface TextOverlay {
  id: string;
  text: string;
  x: number;
  y: number;
  fontSize: number;
  color: string;
  fontWeight: string;
}

const filters: Filter[] = [
  { id: 'none', name: 'Original', cssFilter: 'none' },
  { id: 'vintage', name: 'Vintage', cssFilter: 'sepia(0.5) contrast(1.2)' },
  { id: 'noir', name: 'Noir', cssFilter: 'grayscale(1) contrast(1.3)' },
  { id: 'warm', name: 'Warm', cssFilter: 'saturate(1.3) hue-rotate(-10deg)' },
  { id: 'cool', name: 'Cool', cssFilter: 'saturate(1.2) hue-rotate(10deg)' },
  { id: 'vibrant', name: 'Vibrant', cssFilter: 'saturate(1.8) contrast(1.1)' },
  { id: 'fade', name: 'Fade', cssFilter: 'brightness(1.1) contrast(0.9)' },
  { id: 'dramatic', name: 'Dramatic', cssFilter: 'contrast(1.5) brightness(0.9)' },
];

const stickers: Sticker[] = [
  { id: '1', emoji: '❤️', name: 'Heart' },
  { id: '2', emoji: '😂', name: 'Laughing' },
  { id: '3', emoji: '🔥', name: 'Fire' },
  { id: '4', emoji: '✨', name: 'Sparkles' },
  { id: '5', emoji: '💯', name: 'Hundred' },
  { id: '6', emoji: '👑', name: 'Crown' },
  { id: '7', emoji: '🎵', name: 'Music' },
  { id: '8', emoji: '💪', name: 'Strong' },
  { id: '9', emoji: '🌟', name: 'Star' },
  { id: '10', emoji: '🎉', name: 'Party' },
  { id: '11', emoji: '😍', name: 'Love' },
  { id: '12', emoji: '🤩', name: 'StarStruck' },
];

interface VideoEditorProps {
  videoFile: File;
  onSave: (editedVideo: Blob, metadata: any) => void;
  onCancel: () => void;
}

export const VideoEditor: React.FC<VideoEditorProps> = ({ videoFile, onSave, onCancel }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeTab, setActiveTab] = useState<'trim' | 'filter' | 'text' | 'stickers' | 'effects'>('filter');
  const [selectedFilter, setSelectedFilter] = useState<Filter>(filters[0]);
  const [textOverlays, setTextOverlays] = useState<TextOverlay[]>([]);
  const [selectedStickers, setSelectedStickers] = useState<Array<{ id: string; emoji: string; x: number; y: number }>>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [videoSrc, setVideoSrc] = useState<string>('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [newText, setNewText] = useState('');
  const [textColor, setTextColor] = useState('#ffffff');
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [saturation, setSaturation] = useState(100);

  useEffect(() => {
    const url = URL.createObjectURL(videoFile);
    setVideoSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [videoFile]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      const dur = videoRef.current.duration;
      setDuration(dur);
      setTrimEnd(dur);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      if (videoRef.current.currentTime >= trimEnd) {
        videoRef.current.pause();
        videoRef.current.currentTime = trimStart;
        setIsPlaying(false);
      }
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        if (videoRef.current.currentTime >= trimEnd) {
          videoRef.current.currentTime = trimStart;
        }
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

  const addTextOverlay = () => {
    if (newText.trim()) {
      setTextOverlays([
        ...textOverlays,
        {
          id: Date.now().toString(),
          text: newText,
          x: 50,
          y: 50,
          fontSize: 32,
          color: textColor,
          fontWeight: 'bold',
        },
      ]);
      setNewText('');
      setShowTextInput(false);
    }
  };

  const removeTextOverlay = (id: string) => {
    setTextOverlays(textOverlays.filter((t) => t.id !== id));
  };

  const addSticker = (sticker: Sticker) => {
    setSelectedStickers([
      ...selectedStickers,
      {
        id: Date.now().toString(),
        emoji: sticker.emoji,
        x: Math.random() * 60 + 20,
        y: Math.random() * 60 + 20,
      },
    ]);
  };

  const removeSticker = (id: string) => {
    setSelectedStickers(selectedStickers.filter((s) => s.id !== id));
  };

  const handleSave = async () => {
    // In a real implementation, you would:
    // 1. Use a library like ffmpeg.wasm to apply filters and effects
    // 2. Trim the video
    // 3. Overlay text and stickers
    // 4. Export the final video

    const metadata = {
      filter: selectedFilter.id,
      textOverlays,
      stickers: selectedStickers,
      trim: { start: trimStart, end: trimEnd },
      adjustments: { brightness, contrast, saturation },
    };

    // For now, we'll just pass the original file
    // In production, you'd process the video here
    onSave(videoFile, metadata);
  };

  const formatTime = (time: number): string => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCombinedFilter = () => {
    const base = selectedFilter.cssFilter !== 'none' ? selectedFilter.cssFilter : '';
    const adjustments = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`;
    return base ? `${base} ${adjustments}` : adjustments;
  };

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-800 rounded-full transition"
          >
            <X className="w-6 h-6 text-white" />
          </button>
          <h2 className="text-white text-lg font-semibold">Edit Video</h2>
        </div>
        <button
          onClick={handleSave}
          className="px-6 py-2 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition flex items-center space-x-2"
        >
          <Check className="w-5 h-5" />
          <span>Save</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Preview */}
        <div className="flex-1 flex items-center justify-center bg-black p-4">
          <div className="relative max-w-full max-h-full" style={{ aspectRatio: '9/16' }}>
            <video
              ref={videoRef}
              src={videoSrc}
              className="w-full h-full object-contain"
              style={{ filter: getCombinedFilter() }}
              onLoadedMetadata={handleLoadedMetadata}
              onTimeUpdate={handleTimeUpdate}
              playsInline
            />

            {/* Text Overlays */}
            {textOverlays.map((overlay) => (
              <div
                key={overlay.id}
                className="absolute cursor-move"
                style={{
                  left: `${overlay.x}%`,
                  top: `${overlay.y}%`,
                  fontSize: `${overlay.fontSize}px`,
                  color: overlay.color,
                  fontWeight: overlay.fontWeight,
                  textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
                  transform: 'translate(-50%, -50%)',
                }}
              >
                {overlay.text}
                <button
                  onClick={() => removeTextOverlay(overlay.id)}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs"
                >
                  ×
                </button>
              </div>
            ))}

            {/* Stickers */}
            {selectedStickers.map((sticker) => (
              <div
                key={sticker.id}
                className="absolute cursor-move text-4xl"
                style={{
                  left: `${sticker.x}%`,
                  top: `${sticker.y}%`,
                  transform: 'translate(-50%, -50%)',
                }}
              >
                {sticker.emoji}
                <button
                  onClick={() => removeSticker(sticker.id)}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white text-xs"
                >
                  ×
                </button>
              </div>
            ))}

            {/* Playback Controls */}
            <div className="absolute bottom-4 left-4 right-4">
              <div className="bg-black bg-opacity-50 backdrop-blur-sm rounded-lg p-3">
                <div className="flex items-center space-x-3 mb-2">
                  <button onClick={togglePlay} className="text-white">
                    {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                  </button>
                  <button onClick={toggleMute} className="text-white">
                    {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
                  </button>
                  <div className="flex-1">
                    <input
                      type="range"
                      min={trimStart}
                      max={trimEnd}
                      value={currentTime}
                      onChange={(e) => {
                        if (videoRef.current) {
                          videoRef.current.currentTime = parseFloat(e.target.value);
                        }
                      }}
                      className="w-full"
                    />
                  </div>
                  <span className="text-white text-sm">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Editing Tools Sidebar */}
        <div className="w-80 bg-gray-900 border-l border-gray-700 flex flex-col">
          {/* Tabs */}
          <div className="grid grid-cols-5 border-b border-gray-700">
            {[
              { key: 'trim', icon: <Scissors className="w-5 h-5" />, label: 'Trim' },
              { key: 'filter', icon: <Palette className="w-5 h-5" />, label: 'Filter' },
              { key: 'text', icon: <Type className="w-5 h-5" />, label: 'Text' },
              { key: 'stickers', icon: <Smile className="w-5 h-5" />, label: 'Stickers' },
              { key: 'effects', icon: <Wand2 className="w-5 h-5" />, label: 'Effects' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex flex-col items-center justify-center py-3 transition ${
                  activeTab === tab.key
                    ? 'bg-gray-800 text-blue-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {tab.icon}
                <span className="text-xs mt-1">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'trim' && (
              <div className="space-y-4">
                <h3 className="text-white font-semibold mb-3">Trim Video</h3>
                <div>
                  <label className="text-gray-400 text-sm block mb-2">Start Time</label>
                  <input
                    type="range"
                    min="0"
                    max={duration}
                    value={trimStart}
                    onChange={(e) => setTrimStart(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-white text-sm mt-1">{formatTime(trimStart)}</div>
                </div>
                <div>
                  <label className="text-gray-400 text-sm block mb-2">End Time</label>
                  <input
                    type="range"
                    min="0"
                    max={duration}
                    value={trimEnd}
                    onChange={(e) => setTrimEnd(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-white text-sm mt-1">{formatTime(trimEnd)}</div>
                </div>
                <div className="text-gray-400 text-sm">
                  Duration: {formatTime(trimEnd - trimStart)}
                </div>
              </div>
            )}

            {activeTab === 'filter' && (
              <div className="space-y-4">
                <h3 className="text-white font-semibold mb-3">Filters</h3>
                <div className="grid grid-cols-2 gap-3">
                  {filters.map((filter) => (
                    <button
                      key={filter.id}
                      onClick={() => setSelectedFilter(filter)}
                      className={`p-3 rounded-lg border-2 transition ${
                        selectedFilter.id === filter.id
                          ? 'border-blue-500 bg-blue-500 bg-opacity-20'
                          : 'border-gray-700 hover:border-gray-600'
                      }`}
                    >
                      <div
                        className="w-full h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded mb-2"
                        style={{ filter: filter.cssFilter }}
                      />
                      <div className="text-white text-sm font-medium">{filter.name}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'text' && (
              <div className="space-y-4">
                <h3 className="text-white font-semibold mb-3">Text Overlays</h3>
                {!showTextInput ? (
                  <button
                    onClick={() => setShowTextInput(true)}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center justify-center space-x-2"
                  >
                    <Type className="w-5 h-5" />
                    <span>Add Text</span>
                  </button>
                ) : (
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={newText}
                      onChange={(e) => setNewText(e.target.value)}
                      placeholder="Enter text..."
                      className="w-full px-3 py-2 bg-gray-800 text-white border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
                      autoFocus
                    />
                    <div>
                      <label className="text-gray-400 text-sm block mb-1">Text Color</label>
                      <input
                        type="color"
                        value={textColor}
                        onChange={(e) => setTextColor(e.target.value)}
                        className="w-full h-10 rounded"
                      />
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={addTextOverlay}
                        className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        Add
                      </button>
                      <button
                        onClick={() => {
                          setShowTextInput(false);
                          setNewText('');
                        }}
                        className="flex-1 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
                <div className="space-y-2">
                  {textOverlays.map((overlay) => (
                    <div
                      key={overlay.id}
                      className="p-3 bg-gray-800 rounded-lg flex items-center justify-between"
                    >
                      <span className="text-white truncate">{overlay.text}</span>
                      <button
                        onClick={() => removeTextOverlay(overlay.id)}
                        className="text-red-500 hover:text-red-400"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'stickers' && (
              <div className="space-y-4">
                <h3 className="text-white font-semibold mb-3">Stickers</h3>
                <div className="grid grid-cols-4 gap-3">
                  {stickers.map((sticker) => (
                    <button
                      key={sticker.id}
                      onClick={() => addSticker(sticker)}
                      className="aspect-square bg-gray-800 rounded-lg hover:bg-gray-700 transition flex items-center justify-center text-4xl"
                    >
                      {sticker.emoji}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'effects' && (
              <div className="space-y-4">
                <h3 className="text-white font-semibold mb-3">Adjustments</h3>
                <div>
                  <label className="text-gray-400 text-sm block mb-2">Brightness</label>
                  <input
                    type="range"
                    min="50"
                    max="150"
                    value={brightness}
                    onChange={(e) => setBrightness(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-white text-sm mt-1">{brightness}%</div>
                </div>
                <div>
                  <label className="text-gray-400 text-sm block mb-2">Contrast</label>
                  <input
                    type="range"
                    min="50"
                    max="150"
                    value={contrast}
                    onChange={(e) => setContrast(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-white text-sm mt-1">{contrast}%</div>
                </div>
                <div>
                  <label className="text-gray-400 text-sm block mb-2">Saturation</label>
                  <input
                    type="range"
                    min="0"
                    max="200"
                    value={saturation}
                    onChange={(e) => setSaturation(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-white text-sm mt-1">{saturation}%</div>
                </div>
                <button
                  onClick={() => {
                    setBrightness(100);
                    setContrast(100);
                    setSaturation(100);
                  }}
                  className="w-full py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition flex items-center justify-center space-x-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
