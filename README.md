# 🎬 ClipStream - Hybrid AI-Driven Decentralised Video Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.3-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)

> **The Future of Video: Performance Meets Permanence**

ClipStream is a next-generation video sharing platform that combines TikTok-like performance with Web3 efficiency. Experience intelligent AI recommendations, 70% lower storage costs, creator profit-sharing, and true content ownership—all in one platform.

---

## 🌟 Key Features

### 🚀 **Performance & Scalability**
- **Lightning Fast**: CDN-powered delivery with sub-100ms load times globally
- **Hybrid Storage**: Hot content on CDN, cold content on IPFS (70% cost reduction)
- **Redis Caching**: Sub-50ms feed response times
- **Adaptive Streaming**: 4 quality levels (360p to 1080p) with automatic bitrate selection

### 🤖 **AI-Powered Intelligence**
- **Near Real-Time Personalisation**: Swipe events update your preference model in ~100ms via SSE — the feed adapts within a single session
- **TikTok-Style Ranking Model**: 3-component scoring (60% user interest · 30% video quality · 10% exploration bonus)
- **CLIP Embeddings**: 512-dimensional semantic video understanding for precise content matching
- **Whisper Captions**: Automatic subtitle generation in multiple languages
- **Content Moderation**: AI-powered NSFW, violence, and toxicity detection
- **Exploration via UCB**: Upper Confidence Bound bonus surfaces undiscovered categories and prevents filter bubbles

### 🌐 **Web3 & Decentralisation**
- **IPFS Integration**: Permanent, censorship-resistant content storage
- **Filecoin Archival**: Long-term video preservation with proof of storage
- **$WATCH Token**: ERC-20 token on Polygon for creator rewards
- **Verifiable Ownership**: Permanent IPFS CIDs ensure true creator control

### 💰 **Creator Monetisation**
- **Virtual Gifts**: Real-time tipping system with instant payouts
- **Profit Sharing**: 80% of platform revenue distributed to creators
- **Token Rewards**: Quarterly $WATCH token distributions via Merkle trees
- **Transparent Earnings**: Real-time dashboard with detailed analytics

### 🌍 **Internationalisation**
- **8 Languages Supported**: English, Spanish, French, German, Chinese, Japanese, Arabic, Russian
- **Real-time Translation**: Complete UI and content translation
- **RTL Support**: Full right-to-left language support for Arabic

---

## 🧠 ByteDance Monolith Model — TikTok-Scale Recommendation

ClipStream implements Phase 1 of ByteDance's production recommendation system from the paper:

> **Monolith: Real Time Recommendation System With Collisionless Embedding Table**  
> ByteDance (TikTok's parent company) — [arXiv:2209.07663](https://arxiv.org/abs/2209.07663)

This is the actual architecture powering TikTok's "For You" page, adapted for an open-source stack.

### What's Implemented (Phase 1 — Memory Optimization)

| Feature | Description | Memory Savings |
|---|---|---|
| **Collisionless Embedding Table** | SHA-256 hashing (stronger than Monolith's Cuckoo hashing) — zero embedding collisions | Correctness guarantee |
| **Default Category Embeddings** | 16 pre-computed category embeddings for new/cold-start videos — instant recommendations | 99% for new videos |
| **Frequency Filtering** | Dedicated embeddings only for videos with ≥ 10 interactions; others fall back to category default | 90% overall |
| **Expirable Embeddings (TTL)** | 30-day TTL — embeddings not accessed in 30 days are pruned automatically | 95% for long-running deployments |

**Combined result at TikTok scale (10M videos / 1 year):**
```
Without Monolith:  5.12 GB  (10M embeddings × 128 floats × 4 bytes)
With Phase 1:       256 MB  (frequency filter + TTL + category defaults)
Savings: 95%
```

### Near Real-Time Preference Updates (~100ms)

```
User Swipes → Redis Stream → ML Worker → User Profile Updated → SSE Broadcast → Feed Re-ranked
```

Scoring formula (runs on every feed request against the latest user profile):
```python
final_score = (
    0.6 * user_interest_score   # category affinity + CLIP cosine similarity + watch history
  + 0.3 * video_quality_score   # engagement rate (Laplace-smoothed) + age decay + virality
  + 0.1 * exploration_bonus     # UCB discovery bonus — prevents filter bubbles
)
```

### Phase 2 (Planned) — Online Training

The remaining Monolith feature: automatic model retraining every 60 seconds from live interaction events. Currently, interactions update the user profile in real time but the underlying model is not retrained online.

### Embedding API

```bash
GET  /api/v1/embeddings/categories              # list 16 category defaults
GET  /api/v1/embeddings/default/{category}      # get default embedding for a category
GET  /api/v1/embeddings/should-create/{video_id}?interaction_count=N
POST /api/v1/embeddings/cleanup-expired         # prune TTL-expired embeddings (run daily via cron)
GET  /api/v1/embeddings/stats                   # memory usage + TTL stats
```

Implementation: [backend/app/embeddings.py](backend/app/embeddings.py) · [backend/api/embeddings_api.py](backend/api/embeddings_api.py)

---

## 🏗️ Architecture

### **System Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ React Web App│  │  Mobile App  │  │   Admin UI   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Nginx)                       │
│  • Rate Limiting  • SSL/TLS  • Load Balancing               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                                   │  │
│  │  • Auth  • Videos  • Users  • Feed  • Monetisation   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────┐  ┌──────────────┐
│  SurrealDB   │  │  Redis   │  │     IPFS     │
│  (Database)  │  │ (Cache)  │  │   (Storage)  │
└──────────────┘  └────┬─────┘  └──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Celery Workers  │
              │  • Encoding     │
              │  • AI Pipeline  │
              │  • IPFS Upload  │
              │  • Moderation   │
              └─────────────────┘
```

### **Technology Stack**

#### **Frontend**
- **Framework**: React 18.3 with TypeScript 5.5
- **Build Tool**: Vite 5.4
- **Styling**: Tailwind CSS 3.4
- **State Management**: React Context API
- **Icons**: Lucide React
- **QR Codes**: qrcode.react
- **Authentication**: SurrealDB-backed identity service + OAuth bridging

#### **Backend**
- **API Framework**: FastAPI 0.104
- **Database**: SurrealDB (multi-model: documents + graphs + vectors)
- **Cache**: Redis 7 (with LRU eviction)
- **Task Queue**: Celery 5.3 with Redis broker
- **Monitoring**: Flower 2.0
- **Storage**: IPFS (Kubo) + Filecoin

#### **AI/ML Pipeline**
- **Video Encoding**: FFmpeg with adaptive bitrate
- **Speech-to-Text**: OpenAI Whisper
- **Video Embeddings**: OpenAI CLIP
- **Content Moderation**: Custom ML models

#### **Blockchain**
- **Network**: Polygon (MATIC)
- **Token Standard**: ERC-20 ($WATCH)
- **Smart Contracts**: Solidity
- **Distribution**: Merkle tree-based claims

---

## 📦 Project Structure

```
clipstream/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Auth/        # Authentication components
│   │   │   ├── Feed/        # Video feed components
│   │   │   ├── Landing/     # Landing page
│   │   │   ├── Layout/      # Layout components
│   │   │   ├── Mobile/      # Mobile-specific components
│   │   │   ├── Monetisation/# Gift & payment components
│   │   │   ├── Profile/     # User profile components
│   │   │   ├── Share/       # Sharing components
│   │   │   └── Upload/      # Video upload components
│   │   ├── contexts/        # React contexts
│   │   │   ├── AuthContext.tsx
│   │   │   └── LanguageContext.tsx
│   │   ├── lib/             # Utilities & configs
│   │   │   ├── i18n.ts      # Internationalisation
│   │   │   ├── surrealdb.ts # SurrealDB compatibility + client helpers
│   │   │   └── database.types.ts
│   │   ├── App.tsx          # Main app component
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # FastAPI Python backend
│   ├── api/                 # API routes
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── videos.py        # Video endpoints
│   │   ├── users.py         # User endpoints
│   │   └── feed.py          # Feed endpoints
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   │   ├── video_service.py
│   │   ├── ai_service.py
│   │   └── ipfs_service.py
│   ├── workers/             # Celery workers
│   │   ├── video_worker.py  # Video processing
│   │   └── ai_worker.py     # AI pipeline
│   ├── utils/               # Utilities
│   ├── main.py              # FastAPI app
│   └── requirements.txt
│
├── contracts/               # Smart contracts
│   └── WatchToken.sol       # ERC-20 token contract
│
├── scripts/                 # Utility scripts
│   └── init_schema.sh       # Database initialisation
│
├── data/                    # Persistent data
│   ├── surrealdb/          # Database files
│   ├── redis/              # Redis persistence
│   ├── ipfs/               # IPFS data
│   └── uploads/            # Temporary uploads
│
├── docker-compose.yml       # Docker orchestration
├── README.md               # This file
└── docs/COMPLETE_SYSTEM_SUMMARY.md  # Detailed system docs (see docs/README.md)
```

## 📚 Documentation Hub

Every architecture overview, deployment checklist, and troubleshooting note now
lives inside [`docs/`](docs/README.md). Start with the index to jump to:

- `ARCHITECTURE.md` for diagrams + data flows
- `FRONTEND_MOBILE_API_GUIDE.md` for client integration examples
- `PRODUCTION_DEPLOYMENT.md` / `CLOUD_RUN_DEPLOYMENT.md` for rollout steps
- `TESTING_GUIDE.md` for manual + automated test matrices

Historical Supabase references were scrubbed—everything in `docs/` now reflects
the SurrealDB-first, TikTok-style dApp architecture.

---

## 🚀 Quick Start

### **Prerequisites**

- **Node.js** 18+ and npm/yarn
- **Python** 3.11+
- **Docker** & Docker Compose
- **Git**

### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/clipstream.git
cd clipstream
```

### **2. Start Infrastructure Services**

```bash
# Start SurrealDB, Redis, and IPFS
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### **3. Setup Backend**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create or copy the env file (repo ships with backend/.env defaults)
cp .env .env.local  # optional: keep a local override
# Edit backend/.env (or .env.local) with your configuration

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# In another terminal, start Celery worker
celery -A workers.video_worker worker --loglevel=info

# In another terminal, start Celery beat
celery -A workers.video_worker beat --loglevel=info
```

### **Local Dev Stack (Docker Compose)**

Spin everything up locally—even if you also run against cloud databases—so you
can reproduce the full flow end-to-end before touching shared environments:

1. **Prep env files**
   ```bash
   cp backend/.env backend/.env.local   # optional overrides
   cp frontend/.env frontend/.env.local
   ```
   Update `backend/.env` with any secrets/keys. Docker Compose mounts that file
   into the backend, Celery worker, beat, and Flower containers automatically.

2. **Start the core services**
   ```bash
   docker-compose up -d surrealdb redis ipfs
   docker-compose up -d backend celery-worker celery-beat flower
   ```

3. **Tail logs & verify health**
   ```bash
   docker-compose logs -f backend
   curl http://localhost:8080/docs  # FastAPI docs should load
   ```

4. **Run the frontend locally (talking to the containerized backend)**
   ```bash
   cd frontend
   npm install
   VITE_API_BASE_URL=http://localhost:8080 npm run dev
   ```

5. **Exercise the pipeline**
   ```bash
   python test/test_e2e_mobile_flow.py --backend http://localhost:8080
   ```

Stop the stack with `docker-compose down` (add `-v` to clear data).

### **4. Setup Frontend**

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install

# Create or copy the env file (frontend/.env already contains sane defaults)
cp .env .env.local  # optional
# Update Vite env vars with your backend URL and OAuth keys (no Supabase needed)

# Start development server
npm run dev
# or
yarn dev
```

### **5. Access the Application**

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Redis**: localhost:6379
- **IPFS Gateway**: http://localhost:8080
- **IPFS API**: http://localhost:5001
- **Flower (Celery Monitor)**: http://localhost:5555

---

## 🔧 Configuration

### **Environment Variables**

#### **Frontend (.env)**
```env
VITE_API_BASE_URL=http://localhost:8080
VITE_BACKEND_URL=http://localhost:8080 # optional legacy alias used by some scripts
```

#### **Backend (.env)**
```env
# Database
SURREALDB_URL=ws://surrealdb:8000/rpc
SURREALDB_USER=root
SURREALDB_PASS=root
SURREALDB_NS=clipstream
SURREALDB_DB=main

# Redis
REDIS_URL=redis://localhost:6379/0

# IPFS
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=http://localhost:8080

# Blockchain
POLYGON_RPC_URL=https://polygon-rpc.com
WATCH_TOKEN_ADDRESS=0x...
PRIVATE_KEY=your_private_key

# AI Services
OPENAI_API_KEY=your_openai_key

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📚 API Documentation

### **Authentication**

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "johndoe",
  "display_name": "John Doe"
}
```

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### **Video Upload**

```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "file": <video_file>,
  "title": "My Awesome Video"
}
```

### **Get Feed**

```http
GET /api/v1/feed/for-you?page=1&limit=20
Authorization: Bearer <token>
```

For complete API documentation, visit: http://localhost:8080/docs

---

## 🎨 Features in Detail

### **1. Video Upload & Processing**

- **Resumable Uploads**: Powered by tus.io protocol - never lose upload progress
- **Multi-Quality Encoding**: Automatic generation of 360p, 480p, 720p, 1080p versions
- **Thumbnail Generation**: AI-powered thumbnail selection from key frames
- **Metadata Extraction**: Automatic extraction of duration, resolution, codec info
- **Progress Tracking**: Real-time upload and processing status updates

### **2. Near Real-Time TikTok-Style Recommendation Model**

Every swipe instantly updates the user preference model (~100ms end-to-end via SSE):

```
User Swipes → Event Logged → ML Profile Updated → SSE Push → Feed Re-ranked
```

**Scoring formula:**
```python
final_score = (
    0.6 * user_interest_score   # category affinity + CLIP cosine similarity + watch history
  + 0.3 * video_quality_score   # engagement rate (Laplace-smoothed) + age decay + virality
  + 0.1 * exploration_bonus     # UCB discovery bonus — breaks filter bubbles
)
```

**Diversity re-ranking** penalises consecutive videos from the same category.

- **CLIP Embeddings**: 512-dimensional semantic video understanding
- **Collaborative Filtering**: User behaviour-based recommendations
- **Engagement Signals**: Likes, shares, watch time, rewatch, completion rate
- **Virality Score**: Real-time calculation based on share velocity
- **Personalised Feed**: "For You" page adapts within a single session — no batch retraining needed

### **3. Content Moderation**

- **Automated Screening**: Pre-upload content analysis
- **NSFW Detection**: Adult content filtering
- **Violence Detection**: Graphic content identification
- **Toxicity Analysis**: Harmful language detection
- **Manual Review Queue**: Flagged content for human review

### **4. Monetisation System**

#### **Virtual Gifts**
- Rose (10 coins) 🌹
- Star (50 coins) ⭐
- Sparkle (100 coins) ✨
- Trophy (500 coins) 🏆
- Crown (1000 coins) 👑

#### **Creator Earnings**
- **Gift Revenue**: 70% of gift value goes to creator
- **Platform Share**: 80% of net revenue distributed quarterly
- **Token Rewards**: $WATCH tokens via Merkle tree claims
- **Instant Payouts**: Real-time balance updates

### **5. Social Features**

- **Follow System**: Follow creators and get personalised feed
- **Comments**: Threaded discussions on videos
- **Likes & Shares**: Engagement tracking
- **QR Code Sharing**: Easy video sharing via QR codes
- **Profile Customisation**: Avatar, bio, display name

### **6. Internationalisation (i18n)**

**Supported Languages:**
- 🇺🇸 English
- 🇪🇸 Spanish (Español)
- 🇫🇷 French (Français)
- 🇩🇪 German (Deutsch)
- 🇨🇳 Chinese (中文)
- 🇯🇵 Japanese (日本語)
- 🇸🇦 Arabic (العربية)
- 🇷🇺 Russian (Русский)

**Features:**
- Complete UI translation
- RTL support for Arabic
- Language persistence in localStorage
- Real-time language switching

## 💼 Business Model

- **Value Proposition**: TikTok-speed creation with on-chain, SurrealDB-backed
  ownership metadata so influencers can provably control their catalog while
  brands get auditable engagement + compliance data.
- **Revenue Streams**:
  1. **Live micro-payments** via gifts and tips (real-time USDC settlement).
  2. **Creator Ad Share** — 45% of short-form ads + in-feed shopping referrals.
  3. **Licensing + IP Vault** — mint trending clips as collectible drops or
     limited commercial licenses.
  4. **Insights-as-a-Service** — anonymized trend data packages for agencies.
- **Incentives & Tokenomics**: $WATCH tokens reward views, retention, and
  MCP/LLM-verified brand-safe uploads. SurrealDB’s multi-model graph keeps the
  reputation state machine (view graph + payout ledger) in one place.
- **Influencer Offering**:
  - Guaranteed 80%+ net revenue share, tiered boosts for co-branded campaigns.
  - Automated contract + campaign fulfillment dashboards fed by the MCP
    verification events so creators can ship sponsored content with confidence.
  - Cross-post automation to existing socials plus IPFS/Filecoin backup that
    protects evergreen content.
- **Market Flywheel**: More verified uploads → richer multi-modal embeddings →
  better discovery → more watch time → more gift/ad revenue feeding the creator
  pool, making it attractive for the next wave of influencers and advertisers.

---

## 🔐 Security

### **Authentication & Authorisation**
- JWT-based authentication
- Secure password hashing with bcrypt
- OAuth 2.0 support (Google, GitHub, Twitter)
- Session management with Redis
- CSRF protection

### **Data Protection**
- HTTPS/TLS encryption in transit
- Database encryption at rest
- Secure file upload validation
- Rate limiting on all endpoints
- Input sanitisation and validation

### **Content Security**
- IPFS content addressing (immutable CIDs)
- Blockchain-verified ownership
- Decentralised storage (censorship-resistant)
- Automated backup to Filecoin

---

## 📊 Performance Metrics

### **Target Performance**
- **Feed Load Time**: < 100ms (with Redis cache)
- **Video Start Time**: < 500ms (CDN delivery)
- **Upload Processing**: < 2 minutes (for 1080p video)
- **API Response Time**: < 50ms (p95)
- **Concurrent Users**: 10,000+ (horizontal scaling)

### **Storage Efficiency**
- **CDN Storage**: Hot content (last 30 days)
- **IPFS Storage**: Warm content (30-90 days)
- **Filecoin Archive**: Cold content (90+ days)
- **Cost Reduction**: 70% vs traditional cloud storage

### **Caching Strategy**
- **Redis Cache**: Feed data, user profiles, video metadata
- **CDN Cache**: Video files, thumbnails, static assets
- **Browser Cache**: UI assets, translations
- **Cache Invalidation**: Event-driven updates

---

## 🧪 Testing

### **Run Tests**

```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
cd backend
pytest

# E2E tests
npm run test:e2e
```

### **Mobile → Upload → MCP/LLM Harness**

Run the automated pipeline that signs in like the mobile app, uploads a sample
clip, waits for SurrealDB to surface the record, and persists the LLM/MCP
verdict via the new moderation endpoint:

```bash
python test/test_e2e_mobile_flow.py \
  --backend http://localhost:8080 \
  --video path/to/sample.mp4  # optional when ffmpeg is available
```

The harness reuses the SurrealDB compatibility layer, fetches context with the
MCP client, and records an `llm_verification` object on the video so creators
and reviewers can see the status inside the app immediately.

### **Test Coverage**
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Load testing with Locust
- Security testing with OWASP ZAP

---

## 🚢 Deployment

### **Production Deployment**

#### **Option 1: Docker Compose (Simple)**

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

#### **Option 2: Kubernetes (Scalable)**

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n clipstream
```

#### **Option 3: Cloud Platforms**

**Frontend:**
- Vercel (recommended)
- Netlify
- AWS Amplify
- Cloudflare Pages

**Backend:**
- AWS ECS/EKS
- Google Cloud Run
- DigitalOcean App Platform
- Railway

**Database & Cache:**
- SurrealDB Cloud
- Redis Cloud
- AWS ElastiCache

**Storage:**
- Pinata (IPFS pinning)
- Web3.Storage
- Fleek

### **Environment-Specific Configs**

```bash
# Development
npm run dev

# Staging
npm run build:staging
npm run preview

# Production
npm run build
npm run start
```

---

## 🛠️ Development

### **Code Style**

```bash
# Frontend linting
npm run lint
npm run lint:fix

# Backend linting
black backend/
flake8 backend/
mypy backend/

# Type checking
npm run typecheck
```

### **Git Workflow**

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Commit changes
git commit -m "feat: add amazing feature"

# Push to remote
git push origin feature/amazing-feature

# Create pull request
```

### **Commit Convention**

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or auxiliary tool changes

---

## 📈 Roadmap

### **Phase 1: MVP (Completed ✅)**
- [x] User authentication
- [x] Video upload & playback
- [x] Basic feed algorithm
- [x] Profile management
- [x] Comments & likes

### **Phase 2: AI & Monetisation (Completed ✅)**
- [x] CLIP-based recommendations
- [x] Whisper auto-captions
- [x] Virtual gift system
- [x] Creator dashboard
- [x] Token integration

### **Phase 3: Web3 Integration (In Progress 🚧)**
- [x] IPFS storage
- [x] $WATCH token contract
- [ ] Filecoin archival
- [ ] NFT minting for viral videos
- [ ] DAO governance

### **Phase 4: Advanced Features (Planned 📋)**
- [ ] Live streaming
- [ ] Duets & stitches
- [ ] AR filters
- [ ] Music library
- [ ] Creator marketplace
- [ ] Mobile apps (iOS/Android)
- [ ] Desktop app (Electron)

---

## 🤝 Join the Build — Developer Call to Action

We are combining two things that have never shipped together in open source:

1. **ByteDance's Monolith architecture** ([arXiv:2209.07663](https://arxiv.org/abs/2209.07663)) — the actual recommendation engine behind TikTok's For You page, implemented open-source with collisionless embeddings, frequency filtering, TTL expiry, and near real-time SSE preference updates (~100ms)

2. **Creator-owned content economics** — an 80% net revenue share, on-chain ownership via IPFS/Filecoin, and a transparent $WATCH token profit-distribution model that treats creators as equity participants, not tenants

The goal: a platform where the content provider *is* the owner — algorithmically competitive with TikTok, economically structured like a creator cooperative.

### What we're building toward

| Layer | Status | What's needed |
|---|---|---|
| Monolith Phase 1 (memory-efficient embeddings) | ✅ Done | — |
| Near real-time SSE preference loop | ✅ Done | — |
| Monolith Phase 2 — online model retraining (60s cycle) | 🚧 Open | ML engineers |
| Filecoin archival + proof-of-storage | 🚧 Open | Web3 engineers |
| DAO governance + on-chain revenue distribution | 🚧 Open | Solidity / tokenomics |
| iOS / Android mobile apps | 🚧 Open | React Native engineers |
| Live streaming layer | 🚧 Open | WebRTC / media engineers |

### If you want to contribute

The most impactful open area right now is **Monolith Phase 2: online training** — closing the loop so the model retrains every 60 seconds from live interaction events, exactly as ByteDance does in production. See [docs/architecture/MONOLITH_ANALYSIS.md](docs/architecture/MONOLITH_ANALYSIS.md) for a full breakdown of what's implemented vs what's missing.

1. Fork the repository
2. Read [docs/architecture/MONOLITH_ANALYSIS.md](docs/architecture/MONOLITH_ANALYSIS.md) and [docs/architecture/MONOLITH_FEATURES_IMPLEMENTED.md](docs/architecture/MONOLITH_FEATURES_IMPLEMENTED.md)
3. Pick an open item from the table above or open an issue with a proposal
4. Submit a PR — we review fast

```bash
git clone https://github.com/inaim/clipstream2
cd clipstream2
bash START_TIKTOK_PLATFORM.sh
```

If you're working on the payment rails or tokenomics layer, see the companion project [TrustedCrypto](https://github.com/al-khwarizme/TrustedCrypto) — an asset-backed, community-owned currency model that aligns with the creator cooperative economics here.

### Development setup

```bash
# Install pre-commit hooks
npm run prepare

# Run development environment
docker-compose up -d
npm run dev
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - CLIP and Whisper models
- **IPFS** - Decentralised storage protocol
- **Filecoin** - Permanent storage network
- **SurrealDB** - Multi-model database
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Tailwind CSS** - Utility-first CSS framework

---

## 📞 Contact & Support

- **Website**: https://clipstream.io
- **Email**: support@clipstream.io
- **Twitter**: [@ClipStreamApp](https://twitter.com/ClipStreamApp)
- **Discord**: [Join our community](https://discord.gg/clipstream)
- **Documentation**: docs/README.md

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/clipstream&type=Date)](https://star-history.com/#yourusername/clipstream&Date)

---

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/clipstream?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/clipstream?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/clipstream)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/clipstream)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/clipstream)

---

<div align="center">

**Made with ❤️ by the ClipStream Team**

[Website](https://clipstream.io) • [Documentation](https://docs.clipstream.io) • [Community](https://discord.gg/clipstream)

</div>
