# ClipStream - Hybrid AI-Driven Decentralized Video Platform

**by FinAI Labz**

A revolutionary TikTok-style video platform combining Web2 performance with Web3 efficiency, featuring AI-powered content discovery, creator profit-sharing, and democratic governance.

---

## 🎯 Vision

ClipStream represents the next evolution in social video platforms by addressing the fundamental challenges of traditional centralized systems:

- **70% Cost Reduction**: Hybrid storage architecture slashes operational expenses
- **True Creator Ownership**: IPFS-based content archival with verifiable CIDs
- **Democratic Governance**: John Lewis-style co-ownership model
- **AI-Powered Discovery**: CLIP embeddings and behavioral ranking
- **Censorship Resistance**: Decentralized storage and distributed control

---

## 🏗️ Architecture Overview

### Hybrid Five-Layer System

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  - TikTok-style swipeable feed                              │
│  - WebRTC upload with tus.io resumable protocol            │
│  - Real-time interactions (likes, comments, shares)         │
│  - Multi-language support (10 languages)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Supabase Backend Layer                     │
│  - PostgreSQL for relational data                           │
│  - Real-time subscriptions                                  │
│  - Row Level Security (RLS) policies                        │
│  - Edge Functions for serverless compute                    │
│  - Storage buckets for video/image assets                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI Processing Layer                       │
│  - Whisper: Automatic speech recognition & captions         │
│  - CLIP: Semantic video understanding & embeddings          │
│  - Custom ranking model: Behavioral feed personalization    │
│  - Content moderation AI                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Hybrid Storage Layer                       │
│                                                              │
│  ┌──────────────────┐         ┌─────────────────┐          │
│  │   CDN (Hot)      │         │   IPFS (Cold)   │          │
│  │  - Fast delivery │         │  - Archival     │          │
│  │  - <100ms loads  │  ───▶   │  - Permanent    │          │
│  │  - Global edge   │ Archive │  - Verifiable   │          │
│  └──────────────────┘         └─────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Creator Partnership Ledger                      │
│  - Revenue tracking (gifting, advertising)                  │
│  - Expense tracking (CDN, storage, compute)                 │
│  - Profit distribution calculations                         │
│  - Transparent on-chain accounting                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔥 Key Features Implemented

### 1. Authentication & User Management
- Email/password authentication via Supabase Auth
- Username uniqueness validation
- Password strength requirements
- Profile management with avatar support
- Bio, location, and social links
- Age verification system

### 2. Video Platform Core
- **Video Upload**: Resumable uploads with progress tracking
- **Video Feed**: Infinite scroll with lazy loading
- **Swipeable Feed**: Mobile-first TikTok-style navigation
- **Video Interactions**:
  - Likes with animation
  - Comments with threading (up to 2 levels)
  - Comment reactions (like, love, fire, clap)
  - Shares with platform selection
  - QR code sharing
- **View Tracking**: Anonymous and authenticated views
- **Content Discovery**: Trending content, user search, hashtags

### 3. Social Features
- **Following System**: Follow/unfollow creators
- **Messaging**: Direct messages between users
- **Notifications**: Real-time activity updates
- **User Profiles**: Customizable creator profiles
- **Content Organization**: Tabs for videos, likes, and stats

### 4. AI Integration (Ready for Implementation)
- **Automatic Captions**: Whisper API integration points
- **Content Embeddings**: CLIP model for semantic understanding
- **Personalized Feed**: Ranking algorithm based on:
  - User interaction history
  - Content similarity (CLIP embeddings)
  - Recency and velocity
  - Creator relationships
- **Content Moderation**: AI-powered safety filters

### 5. Monetization & Creator Economy

#### Virtual Currency System
- Coin-based economy
- Purchase tracking (lifetime bought/spent)
- Real-time balance updates
- Secure transaction ledger

#### Gifting System
- 5 gift types with varying values:
  - Rose (10 coins)
  - Star (50 coins)
  - Sparkle (100 coins)
  - Trophy (500 coins)
  - Crown (1000 coins)
- 70% revenue share to creators
- Optional personal messages
- Video-specific or profile gifts

#### Creator Partnership Ledger
- Transparent financial tracking:
  - Revenue (gifting, advertising)
  - Expenses (operational costs)
  - Distributions (profit sharing)
- Immutable audit trail
- Metadata for detailed analytics

### 6. Creator Tier System

Automatic tier assignment based on engagement:

| Tier | Min Engagement | Min Followers | Min Videos | Voting Weight | Governance |
|------|---------------|---------------|------------|---------------|------------|
| **Bronze** | 0 | 0 | 1 | 1x | ❌ |
| **Silver** | 1,000 | 100 | 5 | 2x | ❌ |
| **Gold** | 10,000 | 1,000 | 20 | 5x | ✅ |
| **Platinum** | 50,000 | 10,000 | 50 | 10x | ✅ |
| **Diamond** | 100,000 | 50,000 | 100 | 20x | ✅ |

**Tier Benefits:**
- Bronze: Basic analytics, standard support
- Silver: Advanced analytics, priority support, early access
- Gold: Governance access, platform insights, custom branding
- Platinum: Full governance rights, revenue bonus, dedicated support
- Diamond: Board access, maximum profit share, platform co-ownership

### 7. Governance System

**Democratic Decision Making:**
- Proposal types: Feature, Policy, Budget, Moderation
- Weighted voting based on creator tier
- Transparent vote counting
- Time-limited voting periods
- Status tracking: Active → Passed/Rejected → Implemented

**Platform Insights (Gold+ Only):**
- Total and active user counts
- Video and view statistics
- Financial overview:
  - Total revenue
  - Total expenses
  - Net profit
- Historical metrics (30-day trends)

### 8. Geolocation & Mobile Features
- Location tagging for videos
- Regional trending content
- GPS-based content discovery
- Mobile-optimized navigation
- Discover page with trending categories
- Inbox for messages and notifications

### 9. Hybrid Storage Architecture

**Hot Storage (CDN)**:
- Immediate streaming for new content
- <100ms global load times
- Edge caching for popular videos
- Automatic compression and optimization

**Cold Storage (IPFS)** - Ready for Integration:
- Videos archived after 30 days of low activity
- Permanent Content Identifiers (CIDs)
- Verifiable ownership via blockchain
- 70% cost reduction vs CDN-only
- Peer-to-peer content distribution

**Archival Workflow** (To Be Implemented):
```
Video Upload → CDN Storage → Monitoring → [30 days low activity]
→ IPFS Archive → CID Generation → Verification → CDN Removal
```

---

## 💾 Database Schema

### Core Tables

**profiles**
- User identity and public information
- Username, bio, avatar, location
- Social links and verification status

**videos**
- Video metadata (title, description, hashtags)
- Interaction counts (views, likes, comments, shares)
- Geolocation and language
- Processing status

**video_views**
- Anonymous and authenticated view tracking
- Timestamp and user agent
- IP-based deduplication

**comments**
- Hierarchical threading (parent/child)
- Rich text content
- Edit/delete tracking

**comment_reactions**
- Reaction types: like, love, fire, clap
- Real-time aggregation

**follows**
- Creator-follower relationships
- Timestamp tracking

**messages**
- Direct messaging between users
- Read receipts
- Soft delete support

### Monetization Tables

**virtual_currency**
- User coin balances
- Purchase and spending history

**gifts**
- Gift transactions
- Sender/recipient tracking
- Video association

**creator_partnership_ledger**
- All financial transactions
- Revenue, expense, distribution types
- Source tracking and metadata

**creator_metrics**
- Aggregated performance data
- Engagement scores
- Profit share percentages

**content_ipfs_archive**
- IPFS CID storage
- File size and verification hashes
- Archive timestamps

### Governance Tables

**creator_tiers**
- Tier definitions and requirements
- Governance weights
- Benefit descriptions

**creator_tier_assignments**
- User tier assignments
- Governance access flags

**governance_proposals**
- Platform improvement proposals
- Voting deadlines
- Status tracking

**governance_votes**
- Weighted vote records
- Vote choices (yes/no/abstain)

**platform_metrics**
- Daily platform statistics
- User growth and engagement
- Financial performance

---

## 🔐 Security & Privacy

### Row Level Security (RLS)
All tables have RLS policies enforcing:
- Users can only modify their own content
- Private messages only viewable by participants
- Platform metrics restricted to governance creators
- Ledger entries read-only for creators

### Authentication
- Secure password hashing via Supabase Auth
- Session-based authentication
- Token refresh handling
- Protected routes and API endpoints

### Data Privacy
- IP addresses hashed for view tracking
- No PII stored in video metadata
- User-controlled profile visibility
- GDPR-compliant data handling

---

## 🚀 Tech Stack

### Frontend
- **React 18**: UI framework with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tooling
- **Tailwind CSS**: Utility-first styling
- **Lucide Icons**: Beautiful icon library

### Backend
- **Supabase**: Backend-as-a-Service
  - PostgreSQL database
  - Real-time subscriptions
  - Row Level Security
  - Edge Functions
  - Storage buckets

### AI/ML (Integration Points)
- **OpenAI Whisper**: Speech-to-text
- **OpenAI CLIP**: Image/video embeddings
- **Custom Models**: Recommendation engine

### Planned Integrations
- **IPFS**: Decentralized storage
- **Filecoin**: Storage incentivization
- **ENS**: Decentralized naming
- **Stripe**: Payment processing

---

## 📊 Monetization Model

### Revenue Streams
1. **Event-Driven Gifting**: 30% platform fee on virtual gifts
2. **Algorithmic Promotion**: Paid content boosting
3. **Creator Subscriptions**: Premium creator tiers
4. **Advertising**: Non-intrusive video ads

### Profit Distribution
```
Platform Revenue
    ↓
Operating Expenses (CDN, Storage, AI Compute, Staff)
    ↓
Net Profit Pool
    ↓
Distributed to Creator-Partners
(Proportional to engagement_score)
```

**Example Calculation:**
```javascript
creator_profit_share = (creator_engagement_score / total_platform_engagement) * net_profit
```

This ensures:
- Creators are incentivized to produce quality content
- Platform efficiency directly benefits creators
- Democratic profit distribution
- Aligned interests between platform and creators

---

## 🎮 Getting Started

### Prerequisites
```bash
Node.js 18+
npm or yarn
Supabase account
```

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd clipstream
```

2. Install dependencies
```bash
npm install
```

3. Configure environment variables
```bash
cp .env.example .env
```

Add your Supabase credentials to `.env`:
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

4. Run database migrations
- Migrations are located in `supabase/migrations/`
- Apply via Supabase CLI or dashboard

5. Start development server
```bash
npm run dev
```

6. Build for production
```bash
npm run build
```

---

## 🗂️ Project Structure

```
clipstream/
├── src/
│   ├── components/
│   │   ├── AI/              # AI assistant components
│   │   ├── Auth/            # Authentication UI
│   │   ├── Feed/            # Video feed components
│   │   ├── Landing/         # Landing page
│   │   ├── Layout/          # Navigation and headers
│   │   ├── Mobile/          # Mobile-specific views
│   │   ├── Monetization/    # Creator dashboard & gifting
│   │   ├── Profile/         # User profiles
│   │   ├── Share/           # Sharing features
│   │   └── Upload/          # Video upload
│   ├── contexts/
│   │   ├── AuthContext.tsx  # Authentication state
│   │   └── LanguageContext.tsx  # i18n state
│   ├── lib/
│   │   ├── supabase.ts      # Supabase client
│   │   ├── i18n.ts          # Translations
│   │   └── database.types.ts  # TypeScript types
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
├── supabase/
│   ├── functions/           # Edge functions
│   └── migrations/          # Database migrations
├── public/                  # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 🧪 Database Functions

### Creator Metrics
```sql
update_creator_metrics() -- Recalculates all creator scores
```

### Tier Assignment
```sql
update_creator_tier() -- Auto-assigns tiers based on performance
```

### Proposal Results
```sql
get_proposal_results(proposal_uuid) -- Calculates voting outcomes
```

### Platform Metrics
```sql
update_platform_metrics() -- Daily metrics snapshot
```

---

## 🔄 Development Roadmap

### Phase 1: Core Platform ✅
- [x] Authentication system
- [x] Video upload and playback
- [x] Social interactions (likes, comments, shares)
- [x] User profiles and following
- [x] Mobile-responsive design

### Phase 2: Monetization ✅
- [x] Virtual currency system
- [x] Gifting and tipping
- [x] Creator partnership ledger
- [x] Revenue tracking

### Phase 3: Governance ✅
- [x] Creator tier system
- [x] Weighted voting
- [x] Platform metrics dashboard
- [x] Proposal management

### Phase 4: AI Integration 🚧
- [ ] Whisper integration for captions
- [ ] CLIP embeddings for video content
- [ ] Personalized recommendation engine
- [ ] Content moderation AI

### Phase 5: Decentralization 📅
- [ ] IPFS integration
- [ ] Automatic archival pipeline
- [ ] CID verification system
- [ ] Blockchain anchoring
- [ ] ENS username resolution

### Phase 6: Advanced Features 📅
- [ ] Live streaming
- [ ] Creator analytics dashboard
- [ ] Advanced content filters
- [ ] Collaborative videos
- [ ] Premium subscriptions

---

## 🌐 Internationalization

Supported languages:
- English
- Spanish
- French
- German
- Italian
- Portuguese
- Chinese
- Japanese
- Korean
- Arabic

Language switching available in header menu.

---

## 📈 Performance Targets

- **Load Time**: <100ms for video start
- **Upload Success Rate**: >99%
- **Concurrent Users**: 100K+
- **Storage Cost**: 70% reduction vs traditional CDN
- **Global Latency**: <50ms to nearest edge

---

## 🤝 Contributing

This is a proprietary project by FinAI Labz. For partnership inquiries, contact the development team.

---

## 📄 License

Copyright © 2025 Issam Naim / FinAI Labz. All rights reserved.

---

## 🔗 Technical Details

### Why Hybrid Architecture?

**Problem**: Traditional platforms face a trade-off:
- Pure Web2 (YouTube, TikTok): Fast but expensive, centralized control
- Pure Web3 (LBRY, DTube): Decentralized but slow, poor UX

**Solution**: Hybrid approach gets the best of both:

| Aspect | Web2 CDN | IPFS | Hybrid |
|--------|----------|------|--------|
| **Speed** | ⚡ <100ms | 🐌 1-5s | ⚡ <100ms |
| **Cost** | 💰💰💰 High | 💰 Low | 💰💰 Medium |
| **Permanence** | ❌ Deletable | ✅ Permanent | ✅ Permanent |
| **Censorship** | ❌ Centralized | ✅ Resistant | ✅ Resistant |
| **UX** | ✅ Excellent | ❌ Poor | ✅ Excellent |

### Storage Cost Analysis

**Traditional CDN-Only Approach:**
```
1 PB storage @ $0.023/GB/month = $23,000/month
1 PB bandwidth @ $0.08/GB = $80,000/month
Total: $103,000/month = $1.236M/year
```

**Hybrid Approach (70% to IPFS after 30 days):**
```
300 GB CDN hot storage = $6,900/month
700 GB IPFS cold storage @ $0.003/GB = $2,100/month
Bandwidth (CDN): $24,000/month
Total: $33,000/month = $396K/year

Savings: $840K/year (68% reduction)
```

### AI Processing Pipeline

**Video Upload Flow:**
```
1. User uploads video → Supabase Storage
2. Edge function triggers AI processing:
   a. Whisper API → Generate captions
   b. CLIP model → Extract embeddings
   c. Moderation API → Safety check
3. Store results in database
4. Update search index
5. Notify user (processing complete)
```

**Feed Ranking Algorithm:**
```javascript
function calculateRankScore(video, user) {
  const recencyScore = decayFunction(video.created_at);
  const velocityScore = video.engagement_rate / video.age;
  const similarityScore = cosineSimilarity(user.interests, video.clip_embedding);
  const socialScore = video.creator_id in user.following ? 2.0 : 1.0;

  return (
    recencyScore * 0.3 +
    velocityScore * 0.3 +
    similarityScore * 0.25 +
    socialScore * 0.15
  );
}
```

### IPFS Integration Plan

**Archival Trigger:**
```sql
-- Identify videos for archival (low activity + age > 30 days)
SELECT * FROM videos
WHERE created_at < NOW() - INTERVAL '30 days'
  AND views_count < 100
  AND NOT EXISTS (
    SELECT 1 FROM content_ipfs_archive WHERE video_id = videos.id
  );
```

**Archive Process:**
1. Download video from CDN
2. Upload to IPFS node
3. Generate CID
4. Store CID in database
5. Verify CID integrity
6. Remove from CDN
7. Update video record with IPFS flag

**Retrieval Process:**
```javascript
async function getVideo(videoId) {
  const video = await db.videos.findById(videoId);

  if (video.ipfs_cid) {
    // Fetch from IPFS gateway
    const url = `https://gateway.ipfs.io/ipfs/${video.ipfs_cid}`;
    return fetch(url);
  } else {
    // Fetch from CDN
    return fetch(video.cdn_url);
  }
}
```

---

## 📞 Contact & Support

- **Creator**: Issam Naim
- **Organization**: FinAI Labz
- **Platform**: ClipStream
- **Type**: Hybrid AI-Driven Decentralized Video Platform

---

Built with ❤️ by FinAI Labz
