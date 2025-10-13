import { useState, useEffect, useRef } from 'react';
import { Sparkles, X, Send, TrendingUp, Users, MapPin, Clock, Video, DollarSign, Rocket, Lightbulb } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface AIRecommendation {
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function AIAssistant() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && user) {
      generateRecommendations();
      if (chatHistory.length === 0) {
        addAssistantMessage(
          "👋 Hi! I'm your ClipStream AI assistant. I can help you:\n\n" +
          "📹 Create engaging videos\n" +
          "🚀 Promote your content\n" +
          "💰 Monetize through gifting & profit-sharing\n" +
          "📊 Analyze your performance\n" +
          "🎯 Find trending topics\n\n" +
          "What would you like to know?"
        );
      }
    }
  }, [isOpen, user]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const addAssistantMessage = (content: string) => {
    setChatHistory(prev => [...prev, {
      role: 'assistant',
      content,
      timestamp: new Date()
    }]);
  };

  const generateRecommendations = async () => {
    setLoading(true);

    const { data: userVideos } = await supabase
      .from('videos')
      .select('id')
      .eq('user_id', user?.id || '');

    const { data: likedVideos } = await supabase
      .from('likes')
      .select('video_id')
      .eq('user_id', user?.id || '')
      .limit(10);

    const { data: viewedVideos } = await supabase
      .from('video_views')
      .select('video_id, watch_duration')
      .eq('user_id', user?.id || '')
      .order('created_at', { ascending: false })
      .limit(20);

    const recs: AIRecommendation[] = [
      {
        title: 'Create Your First Video',
        description: 'Start earning with our profit-sharing model',
        icon: <Video className="w-5 h-5" />,
        action: () => addAssistantMessage('To create a video:\n\n1. Click the + button in the navigation\n2. Upload your video (resumable uploads supported)\n3. Add a catchy title and description\n4. Use trending hashtags\n5. Post during peak hours (7-9 PM)\n\nYour content is automatically archived on IPFS for permanent ownership!'),
      },
      {
        title: 'Monetization Guide',
        description: 'Learn how to earn from your content',
        icon: <DollarSign className="w-5 h-5" />,
        action: () => addAssistantMessage('💰 ClipStream Monetization:\n\n1. **Gifting** - Receive virtual gifts from viewers (70% goes to you!)\n2. **Profit Sharing** - Earn from platform profits based on your engagement\n3. **Promotion** - Boost your videos for more visibility\n\nYou own your content forever via IPFS CIDs. The more engagement you get, the more you earn!'),
      },
      {
        title: 'Trending Topics',
        description: 'Discover what\'s hot right now',
        icon: <TrendingUp className="w-5 h-5" />,
        action: () => console.log('Show trending'),
      },
      {
        title: 'Promotion Tips',
        description: 'Boost your reach and engagement',
        icon: <Rocket className="w-5 h-5" />,
        action: () => addAssistantMessage('🚀 Promotion Strategies:\n\n1. **Post Timing** - Your followers are most active 7-9 PM\n2. **Hashtags** - Use 3-5 relevant trending hashtags\n3. **Engagement** - Reply to comments within first hour\n4. **Consistency** - Post 1-2 times daily\n5. **Cross-promote** - Share on other platforms\n6. **Collaborations** - Partner with similar creators\n\nOur AI analyzes your content with CLIP embeddings to recommend it to the right audience!'),
      },
    ];

    setRecommendations(recs);
    setLoading(false);
  };

  const getAIResponse = (userMessage: string): string => {
    const msg = userMessage.toLowerCase();

    // Video creation help
    if (msg.includes('create') || msg.includes('upload') || msg.includes('video')) {
      return '📹 **Creating Videos on ClipStream:**\n\n' +
        '1. Click the **+** button in navigation\n' +
        '2. Select your video file (resumable uploads supported)\n' +
        '3. Add an engaging title (keep it short & catchy)\n' +
        '4. Write a description with relevant hashtags\n' +
        '5. Choose a thumbnail\n' +
        '6. Post!\n\n' +
        '**Pro Tips:**\n' +
        '• Videos under 60 seconds perform best\n' +
        '• Use trending sounds and hashtags\n' +
        '• Post during peak hours (7-9 PM)\n' +
        '• Your content is automatically archived on IPFS for permanent ownership!';
    }

    // Monetization questions
    if (msg.includes('money') || msg.includes('earn') || msg.includes('monetize') || msg.includes('profit')) {
      return '💰 **ClipStream Monetization:**\n\n' +
        '**1. Virtual Gifting (70% to creators)**\n' +
        '   • Viewers send gifts during videos\n' +
        '   • You keep 70% of gift value\n' +
        '   • Cash out anytime\n\n' +
        '**2. Profit Sharing**\n' +
        '   • Share in platform net profits\n' +
        '   • Based on your engagement score\n' +
        '   • Transparent distribution\n\n' +
        '**3. Paid Promotion**\n' +
        '   • Boost videos for more reach\n' +
        '   • Target specific audiences\n\n' +
        'You own your content forever via IPFS CIDs!';
    }

    // Promotion help
    if (msg.includes('promote') || msg.includes('views') || msg.includes('reach') || msg.includes('grow')) {
      return '🚀 **Growing Your Audience:**\n\n' +
        '**Best Posting Times:**\n' +
        '• Weekdays: 7-9 PM\n' +
        '• Weekends: 11 AM - 2 PM\n\n' +
        '**Hashtag Strategy:**\n' +
        '• Use 3-5 relevant hashtags\n' +
        '• Mix trending + niche tags\n' +
        '• Create your own branded hashtag\n\n' +
        '**Engagement Tips:**\n' +
        '• Reply to comments quickly\n' +
        '• Ask questions in captions\n' +
        '• Collaborate with other creators\n' +
        '• Post consistently (1-2x daily)\n\n' +
        'Our AI uses CLIP embeddings to recommend your content to interested viewers!';
    }

    // Platform features
    if (msg.includes('feature') || msg.includes('how') || msg.includes('work') || msg.includes('platform')) {
      return '✨ **ClipStream Features:**\n\n' +
        '**Hybrid Architecture:**\n' +
        '• Lightning-fast CDN delivery\n' +
        '• IPFS permanent storage\n' +
        '• 70% lower storage costs\n\n' +
        '**AI-Powered:**\n' +
        '• Automatic captions (Whisper AI)\n' +
        '• Smart recommendations (CLIP)\n' +
        '• Content understanding\n\n' +
        '**Creator Benefits:**\n' +
        '• True content ownership\n' +
        '• Profit sharing model\n' +
        '• Resumable uploads\n' +
        '• Multi-language support\n\n' +
        'Ask me about creating, promoting, or monetizing!';
    }

    // Trending content
    if (msg.includes('trend') || msg.includes('popular') || msg.includes('viral')) {
      return '📈 **Trending on ClipStream:**\n\n' +
        'Current hot topics:\n' +
        '• Short tutorials & how-tos\n' +
        '• Behind-the-scenes content\n' +
        '• Quick tips & life hacks\n' +
        '• Entertainment & comedy\n' +
        '• Educational content\n\n' +
        '**Make it Viral:**\n' +
        '• Hook viewers in first 3 seconds\n' +
        '• Use trending sounds\n' +
        '• Add captions for accessibility\n' +
        '• End with a call-to-action\n\n' +
        'Check the Discover page for real-time trends!';
    }

    // Default helpful response
    return '🤔 I can help you with:\n\n' +
      '📹 **Creating Videos** - Upload tips, best practices\n' +
      '💰 **Monetization** - Gifting, profit-sharing, earnings\n' +
      '🚀 **Promotion** - Growing your audience, hashtags\n' +
      '📊 **Analytics** - Understanding your performance\n' +
      '🎯 **Trending** - What\'s popular right now\n' +
      '⚙️ **Platform Features** - How ClipStream works\n\n' +
      'What would you like to know more about?';
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !user) return;

    const userMessage = message.trim();
    setMessage('');

    // Add user message to chat
    setChatHistory(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);

    // Simulate thinking delay
    setLoading(true);
    setTimeout(() => {
      const response = getAIResponse(userMessage);
      addAssistantMessage(response);
      setLoading(false);
    }, 500);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-20 right-4 w-14 h-14 bg-gradient-cyber rounded-full flex items-center justify-center shadow-lg z-40 hover:scale-110 transition-transform animate-pulse"
        title="AI Assistant - Get help with creating, promoting & monetizing"
      >
        <Sparkles className="w-7 h-7 text-white" />
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-end md:items-center md:justify-center">
      <div className="w-full md:max-w-3xl bg-gradient-to-br from-gray-900 to-black rounded-t-3xl md:rounded-3xl shadow-2xl max-h-[90vh] flex flex-col">
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-cyber rounded-full flex items-center justify-center animate-pulse">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">ClipStream AI Assistant</h2>
              <p className="text-sm text-gray-400">Create • Promote • Monetize</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-gray-800 rounded-full transition"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Chat History */}
          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-4 ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                    : 'bg-gradient-to-r from-sky-blue/20 to-cyber-purple/20 border border-sky-blue/30 text-white'
                }`}
              >
                <p className="text-sm whitespace-pre-line">{msg.content}</p>
                <p className="text-xs opacity-60 mt-2">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gradient-to-r from-sky-blue/20 to-cyber-purple/20 border border-sky-blue/30 rounded-2xl p-4">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-sky-blue"></div>
                  <span className="text-white text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />

          {/* Quick Action Recommendations */}
          {chatHistory.length <= 1 && (
            <div className="space-y-3 pt-4">
              <h3 className="text-white font-semibold text-sm flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-yellow-400" />
                Quick Start Guide
              </h3>
              {recommendations.map((rec, index) => (
                <button
                  key={index}
                  onClick={rec.action}
                  className="w-full bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-xl p-4 text-left transition-all hover:scale-[1.02] active:scale-95"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-gradient-cyber rounded-lg flex items-center justify-center flex-shrink-0">
                      {rec.icon}
                    </div>
                    <div className="flex-1">
                      <h4 className="text-white font-semibold mb-1">{rec.title}</h4>
                      <p className="text-gray-400 text-sm">{rec.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Quick Action Buttons */}
          {chatHistory.length > 1 && (
            <div className="pt-4">
              <h3 className="text-white font-semibold text-sm mb-3">Quick Questions</h3>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => {
                    setMessage('How do I create a video?');
                    handleSendMessage();
                  }}
                  className="bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm transition"
                >
                  📹 Create videos
                </button>
                <button
                  onClick={() => {
                    setMessage('How can I monetize?');
                    handleSendMessage();
                  }}
                  className="bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm transition"
                >
                  💰 Monetization
                </button>
                <button
                  onClick={() => {
                    setMessage('How to promote my videos?');
                    handleSendMessage();
                  }}
                  className="bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm transition"
                >
                  🚀 Promotion tips
                </button>
                <button
                  onClick={() => {
                    setMessage('What are trending topics?');
                    handleSendMessage();
                  }}
                  className="bg-gray-800/50 hover:bg-gray-800 border border-gray-700 rounded-lg p-3 text-white text-sm transition"
                >
                  📈 Trending now
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleSendMessage()}
              placeholder="Ask about creating, promoting, or monetizing..."
              className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-full text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-sky-blue"
              disabled={loading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!message.trim() || loading}
              className="w-12 h-12 bg-gradient-cyber rounded-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition hover:scale-105 active:scale-95"
            >
              <Send className="w-5 h-5 text-white" />
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">
            AI-powered assistant with knowledge of ClipStream features
          </p>
        </div>
      </div>
    </div>
  );
}
