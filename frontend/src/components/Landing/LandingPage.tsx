import { Video, Zap, Brain, Database, Lock, Globe, TrendingUp, Users, Play, Upload, Shield, Cpu, DollarSign, Gift, Crown, Sparkles, X, Send } from 'lucide-react';
import { useState } from 'react';
import { TikTokLanguageSelector } from '../Layout/TikTokLanguageSelector';
import { useLanguage } from '../../contexts/LanguageContext';

interface LandingPageProps {
  onGetStarted: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
  const { t } = useLanguage();
  const [activeSection, setActiveSection] = useState('overview');
  const [showAIChat, setShowAIChat] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    element?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setActiveSection('overview');
  };

  const getAIResponse = (userMessage: string): string => {
    const msg = userMessage.toLowerCase();

    if (msg.includes('feature') || msg.includes('what') || msg.includes('about')) {
      return '✨ **ClipStream is a hybrid video platform** combining:\n\n' +
        '• TikTok-like speed with Web3 efficiency\n' +
        '• AI-powered recommendations (CLIP + Whisper)\n' +
        '• 70% lower storage costs via IPFS\n' +
        '• Creator profit-sharing model\n' +
        '• True content ownership\n\n' +
        'Ask me about monetization, features, or how to get started!';
    }

    if (msg.includes('money') || msg.includes('earn') || msg.includes('monetize')) {
      return '💰 **Monetization on ClipStream:**\n\n' +
        '1. **Virtual Gifting** - 70% goes to creators\n' +
        '2. **Profit Sharing** - Share in platform profits\n' +
        '3. **Content Ownership** - Permanent IPFS storage\n\n' +
        'You\'re not just a user—you\'re a partner!';
    }

    if (msg.includes('start') || msg.includes('sign') || msg.includes('join')) {
      return '🚀 **Getting Started is Easy:**\n\n' +
        '1. Click "Get Started" to create your account\n' +
        '2. Set up your profile\n' +
        '3. Start uploading videos\n' +
        '4. Earn from day one!\n\n' +
        'Ready to join? Click the "Get Started" button above!';
    }

    if (msg.includes('ai') || msg.includes('technology') || msg.includes('how')) {
      return '🤖 **Our AI Technology:**\n\n' +
        '• **Whisper AI** - Automatic captions\n' +
        '• **CLIP Embeddings** - Content understanding\n' +
        '• **Smart Recommendations** - Personalized feed\n' +
        '• **IPFS Storage** - Decentralized archival\n\n' +
        'We use cutting-edge AI to enhance your experience!';
    }

    if (msg.includes('cost') || msg.includes('price') || msg.includes('free')) {
      return '💵 **Pricing:**\n\n' +
        '• **Free to join** and start creating\n' +
        '• **No subscription fees**\n' +
        '• **Earn from your content** immediately\n' +
        '• Optional paid promotion for more reach\n\n' +
        'Start earning, not paying!';
    }

    return '👋 **Hi! I\'m the ClipStream AI assistant.**\n\n' +
      'I can help you learn about:\n' +
      '• Platform features\n' +
      '• Monetization opportunities\n' +
      '• AI technology\n' +
      '• Getting started\n\n' +
      'What would you like to know?';
  };

  const handleSendMessage = () => {
    if (!chatMessage.trim()) return;

    const userMsg = chatMessage.trim();
    setChatMessage('');

    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);

    setTimeout(() => {
      const response = getAIResponse(userMsg);
      setChatHistory(prev => [...prev, { role: 'assistant', content: response }]);
    }, 500);
  };

  const openAIChat = () => {
    setShowAIChat(true);
    if (chatHistory.length === 0) {
      setChatHistory([{
        role: 'assistant',
        content: '👋 **Welcome to ClipStream!**\n\n' +
          'I can help you learn about our platform. Ask me about:\n\n' +
          '• Features & technology\n' +
          '• Monetization opportunities\n' +
          '• How to get started\n' +
          '• AI capabilities\n\n' +
          'What would you like to know?'
      }]);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={scrollToTop}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer group"
            >
              <Video className="w-8 h-8 text-blue-600 group-hover:scale-110 transition-transform" />
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent block">
                  ClipStream
                </span>
                <span className="text-xs text-slate-500 font-medium">by FinAI Labz</span>
              </div>
            </button>
            <nav className="hidden md:flex space-x-8">
              {['overview', 'features', 'monetization', 'architecture', 'roadmap'].map((section) => (
                <button
                  key={section}
                  onClick={() => scrollToSection(section)}
                  className={`text-sm font-medium transition pb-1 border-b-2 capitalize ${
                    activeSection === section
                      ? 'text-blue-600 border-blue-600'
                      : 'text-gray-500 hover:text-blue-600 border-transparent'
                  }`}
                >
                  {t(`landing.nav.${section}`)}
                </button>
              ))}
            </nav>
            <div className="flex items-center gap-3">
              <TikTokLanguageSelector variant="header" showText={false} />
              <button
                onClick={onGetStarted}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg font-semibold hover:shadow-lg transition"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <section className="text-center mb-24 py-12">
          <div className="inline-block mb-4 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
            {t('landing.tagline')}
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-slate-900 mb-6">
            {t('landing.heroTitle')}
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              {t('landing.heroSubtitle')}
            </span>
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-8">
            {t('landing.heroDescription')}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onGetStarted}
              className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-bold text-lg hover:shadow-xl transition"
            >
              <Play className="w-5 h-5" />
              {t('landing.startCreating')}
            </button>
            <button
              onClick={() => scrollToSection('features')}
              className="px-8 py-4 bg-white text-gray-900 rounded-xl font-semibold text-lg border-2 border-gray-200 hover:border-blue-600 transition"
            >
              {t('landing.learnMore')}
            </button>
          </div>
        </section>

        <section id="overview" className="mb-24 scroll-mt-24">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">The Hybrid Advantage</h2>
            <p className="text-lg text-slate-600">
              Cherry-picking the best of Web2 performance and Web3 efficiency
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title={t('landing.features.lightningFast.title')}
              description={t('landing.features.lightningFast.description')}
              color="blue"
            />
            <FeatureCard
              icon={<Brain className="w-8 h-8" />}
              title={t('landing.features.aiPowered.title')}
              description={t('landing.features.aiPowered.description')}
              color="purple"
            />
            <FeatureCard
              icon={<Database className="w-8 h-8" />}
              title={t('landing.features.costReduction.title')}
              description={t('landing.features.costReduction.description')}
              color="green"
            />
            <FeatureCard
              icon={<Lock className="w-8 h-8" />}
              title={t('landing.features.verifiableOwnership.title')}
              description={t('landing.features.verifiableOwnership.description')}
              color="red"
            />
          </div>
        </section>

        <section id="features" className="mb-24 scroll-mt-24">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Powerful Features</h2>
            <p className="text-lg text-slate-600">
              Everything you need to create, share, and discover amazing content
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Resumable Uploads</h3>
              <p className="text-slate-600 mb-4">
                Powered by the tus.io protocol, never lose your upload progress. Pause, resume,
                and continue uploading even after network interruptions or browser closures.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full" />
                  Automatic retry on failure
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full" />
                  Resume from any device
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full" />
                  Progress persistence
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">AI Intelligence</h3>
              <p className="text-slate-600 mb-4">
                Our AI layer uses Whisper for automatic captions, CLIP for semantic understanding,
                and custom ranking models for the perfect personalized feed.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" />
                  Automatic transcription
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" />
                  Content vectorization
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-purple-600 rounded-full" />
                  Behavioral ranking
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                <Database className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Hybrid Storage</h3>
              <p className="text-slate-600 mb-4">
                Videos stream instantly from our CDN while being archived to IPFS for permanent,
                cost-efficient storage. Get Web2 speed with Web3 permanence.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-green-600 rounded-full" />
                  Instant CDN playback
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-green-600 rounded-full" />
                  IPFS archival
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-green-600 rounded-full" />
                  Verifiable CID hashes
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mb-4">
                <Globe className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Global Reach</h3>
              <p className="text-slate-600 mb-4">
                Multi-language support with personalized content discovery. Share globally
                while maintaining local relevance for every audience.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-red-600 rounded-full" />
                  10 supported languages
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-red-600 rounded-full" />
                  Regional trending
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-red-600 rounded-full" />
                  Geolocation tagging
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section id="monetization" className="mb-24 scroll-mt-24">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Creator Economy & Monetization</h2>
            <p className="text-lg text-slate-600">
              John Lewis-style co-ownership model with transparent profit sharing
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-600 to-cyan-600 rounded-3xl p-8 md:p-12 text-white mb-8">
            <div className="max-w-3xl mx-auto text-center">
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Crown className="w-10 h-10" />
              </div>
              <h3 className="text-3xl font-bold mb-4">You're Not a User—You're a Partner</h3>
              <p className="text-xl text-blue-100 mb-6">
                Our platform operates on a revolutionary co-ownership model where creators share in the platform's net profits based on their engagement and contribution.
              </p>
              <div className="grid md:grid-cols-3 gap-6 text-left">
                <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                  <div className="text-3xl font-bold mb-2">70%</div>
                  <div className="text-sm text-blue-100">of gifting revenue goes to creators</div>
                </div>
                <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                  <div className="text-3xl font-bold mb-2">100%</div>
                  <div className="text-sm text-blue-100">transparent profit distribution</div>
                </div>
                <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                  <div className="text-3xl font-bold mb-2">∞</div>
                  <div className="text-sm text-blue-100">permanent ownership via IPFS CIDs</div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Revenue Streams</h3>
              <p className="text-slate-600 mb-4">
                Multiple ways for creators to earn while maintaining platform sustainability.
              </p>
              <ul className="space-y-3 text-sm text-slate-600">
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Gift className="w-3 h-3 text-green-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Event-Driven Gifting</div>
                    <div>Users send virtual gifts during streams or as tips with 70% going to creators</div>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <TrendingUp className="w-3 h-3 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Algorithmic Promotion</div>
                    <div>Optional paid promotion for increased visibility and reach</div>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Users className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Profit Partnership</div>
                    <div>Share in platform net profits proportional to your engagement score</div>
                  </div>
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg transition">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Censorship Resistance</h3>
              <p className="text-slate-600 mb-4">
                True ownership and control through decentralized architecture.
              </p>
              <ul className="space-y-3 text-sm text-slate-600">
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Lock className="w-3 h-3 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Verifiable Ownership</div>
                    <div>Content archived on IPFS with permanent CIDs proving ownership</div>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Database className="w-3 h-3 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Decentralized Control</div>
                    <div>Profits distributed among creator-partners prevent single-entity control</div>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Globe className="w-3 h-3 text-green-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">Partnership Ledger</div>
                    <div>All financial events tracked transparently on-chain for accountability</div>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div className="bg-slate-900 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4 text-center">How Profit Distribution Works</h3>
            <div className="max-w-4xl mx-auto">
              <div className="grid md:grid-cols-3 gap-6 mb-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl font-bold">1</span>
                  </div>
                  <h4 className="font-bold mb-2">Platform Efficiency</h4>
                  <p className="text-sm text-slate-300">Platform covers necessary operating expenses (CDN, AI compute, maintenance)</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl font-bold">2</span>
                  </div>
                  <h4 className="font-bold mb-2">Profit Pool</h4>
                  <p className="text-sm text-slate-300">Remaining net revenue is pooled for distribution to creator-partners</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl font-bold">3</span>
                  </div>
                  <h4 className="font-bold mb-2">Proportional Distribution</h4>
                  <p className="text-sm text-slate-300">Profits distributed based on engagement score, content volume, and contribution</p>
                </div>
              </div>
              <div className="bg-white/10 rounded-xl p-4 text-center backdrop-blur-sm">
                <p className="text-sm text-slate-300">
                  Every creator's self-interest is aligned with platform success, maximizing quality and originality of content
                </p>
              </div>
            </div>
          </div>
        </section>

        <section id="architecture" className="mb-24 scroll-mt-24">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Hybrid Architecture Stack</h2>
            <p className="text-lg text-slate-600">
              Five-layer system designed for speed and distributed processing
            </p>
          </div>

          <div className="bg-white p-8 rounded-2xl border border-slate-200 mb-8">
            <div className="flex flex-wrap items-center justify-center gap-4 text-center mb-8">
              <ArchNode label="React Frontend" subtext="WebRTC Upload" />
              <Arrow />
              <ArchNode label="FastAPI Gateway" subtext="Async Python" />
              <Arrow />
              <ArchNode label="Redis Queue" subtext="Task Management" />
              <Arrow />
              <ArchNode label="MongoDB" subtext="Metadata & Cache" />
              <Arrow />
              <ArchNode label="AI Services" subtext="Whisper + CLIP" />
              <Arrow />
              <ArchNode label="CDN Origin" subtext="Fast Delivery" />
              <Arrow />
              <ArchNode label="IPFS Network" subtext="Permanent Archive" />
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <MetricCard
              title="Storage Cost Reduction"
              value="70%"
              description="By moving cold storage to IPFS"
              color="green"
            />
            <MetricCard
              title="CDN Bandwidth Savings"
              value="40%"
              description="Through optimized encoding"
              color="blue"
            />
            <MetricCard
              title="Load Time Improvement"
              value="≤100ms"
              description="Target latency for streams"
              color="purple"
            />
          </div>
        </section>

        <section id="roadmap" className="scroll-mt-24 mb-24">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">MVP Development Roadmap</h2>
            <p className="text-lg text-slate-600">
              Agile phases delivering a functional product quickly
            </p>
          </div>
          <div className="relative">
            <div className="absolute left-1/2 -translate-x-1/2 top-4 bottom-4 w-0.5 bg-slate-200 hidden md:block" />
            <div className="space-y-8">
              <RoadmapItem
                phase="Phase 1"
                duration="4 Weeks"
                title="Core Backend"
                status="Completed"
                items={['FastAPI Gateway', 'MongoDB Database', 'Redis Caching', 'Upload API Skeleton']}
                position="left"
              />
              <RoadmapItem
                phase="Phase 2"
                duration="4 Weeks"
                title="Frontend UI"
                status="Completed"
                items={['React Application', 'WebRTC Upload', 'Infinite Scroll Feed', 'Mobile Responsive']}
                position="right"
              />
              <RoadmapItem
                phase="Phase 3"
                duration="3 Weeks"
                title="AI Integration"
                status="In Progress"
                items={['Whisper Captions', 'CLIP Embeddings', 'Recommendation Engine', 'Content Moderation']}
                position="left"
              />
              <RoadmapItem
                phase="Phase 4"
                duration="3 Weeks"
                title="Decentralization"
                status="Planned"
                items={['IPFS Integration', 'Content Hashing', 'Archival Automation', 'CID Verification']}
                position="right"
              />
              <RoadmapItem
                phase="Phase 5"
                duration="2 Weeks"
                title="Deployment"
                status="Planned"
                items={['Cloud Optimization', 'Security Audit', 'Performance Testing', 'Production Launch']}
                position="left"
              />
            </div>
          </div>
        </section>

        <section className="text-center py-16 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-3xl text-white mb-24">
          <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl mb-8 text-blue-100">
            Join the next generation of video creators
          </p>
          <button
            onClick={onGetStarted}
            className="px-8 py-4 bg-white text-blue-600 rounded-xl font-bold text-lg hover:shadow-2xl transition"
          >
            Create Your Account
          </button>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-slate-600 text-sm mb-2">
            &copy; 2025 Issam Naim / FinAI Labz. All rights reserved.
          </p>
          <p className="text-slate-500 text-xs">
            Hybrid AI-Driven Decentralized Video Platform
          </p>
        </div>
      </footer>

      {/* AI Assistant Button */}
      {!showAIChat && (
        <button
          onClick={openAIChat}
          className="fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full flex items-center justify-center shadow-2xl z-50 hover:scale-110 transition-transform animate-pulse"
          title="Ask AI about ClipStream"
        >
          <Sparkles className="w-8 h-8 text-white" />
        </button>
      )}

      {/* AI Chat Modal */}
      {showAIChat && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end md:items-center md:justify-center">
          <div className="w-full md:max-w-2xl bg-white rounded-t-3xl md:rounded-3xl shadow-2xl max-h-[85vh] flex flex-col">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-gradient-to-r from-blue-600 to-cyan-600 rounded-t-3xl">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">ClipStream AI</h2>
                  <p className="text-sm text-blue-100">Ask me anything about the platform</p>
                </div>
              </div>
              <button
                onClick={() => setShowAIChat(false)}
                className="p-2 hover:bg-white/20 rounded-full transition"
              >
                <X className="w-6 h-6 text-white" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50">
              {chatHistory.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
                        : 'bg-white border border-slate-200 text-slate-900'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-line">{msg.content}</p>
                  </div>
                </div>
              ))}

              {/* Quick Action Buttons */}
              {chatHistory.length <= 1 && (
                <div className="grid grid-cols-2 gap-2 pt-4">
                  <button
                    onClick={() => {
                      setChatMessage('What features does ClipStream have?');
                      handleSendMessage();
                    }}
                    className="bg-white border border-slate-200 hover:border-blue-600 rounded-lg p-3 text-slate-700 text-sm transition"
                  >
                    ✨ Features
                  </button>
                  <button
                    onClick={() => {
                      setChatMessage('How can I earn money?');
                      handleSendMessage();
                    }}
                    className="bg-white border border-slate-200 hover:border-blue-600 rounded-lg p-3 text-slate-700 text-sm transition"
                  >
                    💰 Monetization
                  </button>
                  <button
                    onClick={() => {
                      setChatMessage('How do I get started?');
                      handleSendMessage();
                    }}
                    className="bg-white border border-slate-200 hover:border-blue-600 rounded-lg p-3 text-slate-700 text-sm transition"
                  >
                    🚀 Get Started
                  </button>
                  <button
                    onClick={() => {
                      setChatMessage('Tell me about the AI technology');
                      handleSendMessage();
                    }}
                    className="bg-white border border-slate-200 hover:border-blue-600 rounded-lg p-3 text-slate-700 text-sm transition"
                  >
                    🤖 AI Tech
                  </button>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-200 bg-white rounded-b-3xl">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask about features, monetization, or getting started..."
                  className="flex-1 px-4 py-3 bg-slate-100 border border-slate-200 rounded-full text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!chatMessage.trim()}
                  className="w-12 h-12 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition hover:scale-105"
                >
                  <Send className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FeatureCard({ icon, title, description, color }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}) {
  const colorClasses = {
    blue: 'from-blue-500 to-cyan-500',
    purple: 'from-purple-500 to-pink-500',
    green: 'from-green-500 to-emerald-500',
    red: 'from-red-500 to-orange-500',
  }[color];

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 text-center hover:shadow-xl transition group">
      <div className={`mx-auto w-16 h-16 bg-gradient-to-br ${colorClasses} rounded-2xl flex items-center justify-center text-white mb-4 group-hover:scale-110 transition`}>
        {icon}
      </div>
      <h3 className="font-bold text-xl mb-2 text-slate-900">{title}</h3>
      <p className="text-slate-600 text-sm">{description}</p>
    </div>
  );
}

function ArchNode({ label, subtext }: { label: string; subtext?: string }) {
  return (
    <div className="px-4 py-3 bg-slate-100 border border-slate-200 rounded-lg hover:bg-slate-200 transition cursor-pointer min-w-[140px]">
      <div className="font-semibold text-slate-700 text-sm">{label}</div>
      {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
    </div>
  );
}

function Arrow() {
  return <span className="text-slate-400 text-2xl hidden sm:inline">→</span>;
}

function MetricCard({ title, value, description, color }: {
  title: string;
  value: string;
  description: string;
  color: string;
}) {
  const colorClasses = {
    green: 'from-green-500 to-emerald-500',
    blue: 'from-blue-500 to-cyan-500',
    purple: 'from-purple-500 to-pink-500',
  }[color];

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 text-center">
      <div className={`text-4xl font-black mb-2 bg-gradient-to-r ${colorClasses} bg-clip-text text-transparent`}>
        {value}
      </div>
      <h4 className="font-bold text-slate-900 mb-2">{title}</h4>
      <p className="text-sm text-slate-600">{description}</p>
    </div>
  );
}

function RoadmapItem({
  phase,
  duration,
  title,
  status,
  items,
  position,
}: {
  phase: string;
  duration: string;
  title: string;
  status: string;
  items: string[];
  position: 'left' | 'right';
}) {
  const statusColors = {
    'Completed': 'bg-green-100 text-green-700',
    'In Progress': 'bg-blue-100 text-blue-700',
    'Planned': 'bg-slate-100 text-slate-700',
  }[status];

  return (
    <div className={`md:flex md:items-center ${position === 'right' ? 'md:flex-row-reverse' : ''}`}>
      <div className={`md:w-1/2 ${position === 'left' ? 'md:pr-8 md:text-right' : 'md:pl-8'}`}>
        <div className="inline-block bg-white p-6 rounded-xl border border-slate-200 shadow-sm w-full max-w-sm">
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-2 ${statusColors}`}>
            {status}
          </div>
          <div className="text-blue-600 font-bold mb-1">{phase} • {duration}</div>
          <h4 className="font-bold text-xl text-slate-900 mb-3">{title}</h4>
          <ul className="space-y-1 text-sm text-slate-600">
            {items.map((item, i) => (
              <li key={i} className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-blue-600 rounded-full" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mx-auto md:mx-0 z-10 my-4 md:my-0">
        {phase.split(' ')[1]}
      </div>
    </div>
  );
}
