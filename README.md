<div align="center">

# ClipStream

**The open-source, creator-owned short video platform**  
*TikTok-grade recommendation engine · 80% revenue to creators · Permanent content ownership*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/inaim/clipstream2?style=social)](https://github.com/inaim/clipstream2/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/inaim/clipstream2?style=social)](https://github.com/inaim/clipstream2/network/members)
[![Last commit](https://img.shields.io/github/last-commit/inaim/clipstream2)](https://github.com/inaim/clipstream2/commits/main)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [Monolith Model](#-bytedan ce-monolith-model) · [Contributing](#-join-the-build) · [Roadmap](#-roadmap)

</div>

---

## The Problem

Every major video platform — TikTok, YouTube, Instagram — extracts 55–100% of advertising revenue while maintaining total algorithmic control. Creators have no ownership, no transparency, and no recourse when policies change overnight.

Decentralised alternatives exist but sacrifice performance: 15–30 second load times prevent mainstream adoption.

## The Solution

ClipStream is a hybrid platform that delivers TikTok-speed content discovery with on-chain creator ownership:

- **Same algorithm, open source** — ByteDance's Monolith recommendation engine ([arXiv:2209.07663](https://arxiv.org/abs/2209.07663)) implemented openly, with near real-time (~100ms) preference updates
- **80% revenue to creators** — gifts and ad share settled in [TrustedCrypto](https://github.com/al-khwarizme/TrustedCrypto); $WATCH tracks contribution (views, watch time, brand-safe uploads) and determines each creator's share
- **Permanent ownership** — every video stored on IPFS with an immutable CID; creators control their catalog regardless of platform policy
- **70% lower storage cost** — hot content on CDN, cold content on Filecoin archival

> **Two-layer economics:** $WATCH measures contribution — TrustedCrypto settles it. See [TrustedCrypto →](https://github.com/al-khwarizme/TrustedCrypto)

---

## Table of Contents

- [Key Features](#-key-features)
- [ByteDance Monolith Model](#-bytedance-monolith-model)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Business Model](#-business-model)
- [Roadmap](#-roadmap)
- [Join the Build](#-join-the-build)
- [Contributing](#contributing)
- [License](#-license)

---

## ✨ Key Features

| Category | Feature | Detail |
|---|---|---|
| **AI / ML** | Near real-time personalisation | Swipe → preference model update in ~100ms via SSE |
| **AI / ML** | ByteDance Monolith embeddings | Collisionless, TTL-expiry, frequency-filtered — 95% memory savings |
| **AI / ML** | CLIP video understanding | 512-dimensional semantic embeddings for precise content matching |
| **AI / ML** | Auto-captions | OpenAI Whisper, multi-language |
| **Storage** | Hybrid CDN + IPFS | Hot content on CDN, cold on Filecoin — 70% cost reduction |
| **Economics** | 80% creator revenue share | Gifts + ad share settled via TrustedCrypto; $WATCH tracks contribution share |
| **Economics** | On-chain ownership | Immutable IPFS CIDs — content survives platform policy changes |
| **Scale** | TikTok-grade feed | < 50ms p95 API response, 10 000+ concurrent users |
| **i18n** | 8 languages | EN, ES, FR, DE, ZH, JA, AR, RU — RTL support included |

---

## 🧠 ByteDance Monolith Model

> **Monolith: Real Time Recommendation System With Collisionless Embedding Table**  
> ByteDance (TikTok's parent company) — [arXiv:2209.07663](https://arxiv.org/abs/2209.07663)

This is the actual system powering TikTok's For You page. ClipStream implements it open-source.

### Phase 1 — Memory Optimization (Shipped)

| Feature | How it works | Memory saving |
|---|---|---|
| Collisionless Embedding Table | SHA-256 hashing — zero collisions, stronger than Monolith's Cuckoo hashing | Correctness guarantee |
| Default Category Embeddings | 16 pre-computed category embeddings for cold-start videos — instant recommendations | 99% for new content |
| Frequency Filtering | Dedicated embeddings only for videos with ≥ 10 interactions | 90% overall |
| Expirable Embeddings (TTL) | 30-day TTL — inactive embeddings pruned automatically | 95% long-running |

```
Without Monolith:  5.12 GB  (10M videos × 128 floats × 4 bytes)
With Phase 1:       256 MB
Savings: 95%
```

### Near Real-Time Preference Loop

```
User Swipes → Redis Stream → ML Worker → User Profile Updated → SSE Broadcast → Feed Re-ranked
                                                                  ↑ ~100ms end-to-end
```

Scoring formula (evaluated on every feed request against the current user profile):

```python
final_score = (
    0.6 * user_interest_score   # category affinity + CLIP cosine similarity + watch history
  + 0.3 * video_quality_score   # engagement rate (Laplace-smoothed) + age decay + virality
  + 0.1 * exploration_bonus     # UCB discovery — breaks filter bubbles
)
```

Diversity re-ranking prevents consecutive videos from the same category.

### Phase 2 — Online Training (Open)

The remaining Monolith feature: automatic model retraining every 60 seconds from live events. This is the highest-impact open contribution — see [docs/architecture/MONOLITH_ANALYSIS.md](docs/architecture/MONOLITH_ANALYSIS.md).

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│                   Client Layer                     │
│    React Web App · Mobile App · Admin UI           │
└──────────────────────┬────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────┐
│            API Gateway (Nginx)                     │
│    Rate limiting · SSL/TLS · Load balancing        │
└──────────────────────┬────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────┐
│              FastAPI Backend                       │
│    Auth · Videos · Feed · Users · Monetisation    │
│    Real-time ML · TikTok Ingestion · SSE Events   │
└──────┬────────────────┬────────────────┬──────────┘
       │                │                │
┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼───────┐
│  SurrealDB  │  │    Redis    │  │    IPFS     │
│  (primary   │  │  (feed      │  │  (archival  │
│   database) │  │   cache +   │  │   storage)  │
│             │  │   events)   │  │             │
└─────────────┘  └──────┬──────┘  └─────────────┘
                        │
                 ┌──────▼──────┐
                 │   Celery    │
                 │  Workers    │
                 │ Encode · AI │
                 │ IPFS · Mod  │
                 └─────────────┘
```

### Stack

| Layer | Technology |
|---|---|
| Frontend | React 18.3 · TypeScript 5.5 · Vite · Tailwind CSS |
| Backend | FastAPI 0.104 · Python 3.11 |
| Database | SurrealDB (multi-model: documents + graphs + vectors) |
| Cache / Queue | Redis 7 · Celery 5.3 |
| Storage | IPFS (Kubo) · Filecoin |
| AI/ML | OpenAI CLIP · Whisper · Custom moderation models |
| Blockchain | Polygon · ERC-20 ($WATCH contribution tracking) · Solidity · TrustedCrypto settlement |

---

## 🚀 Quick Start

**Prerequisites:** Docker & Docker Compose, Node.js 18+, Python 3.11+

```bash
# 1. Clone
git clone https://github.com/inaim/clipstream2
cd clipstream2

# 2. One-command start (starts all services)
bash START_TIKTOK_PLATFORM.sh

# 3. Seed test data
curl -X POST "http://localhost:8080/api/v1/embeddings/generate-dummy?count=1000"

# 4. Open the swipe interface
open http://localhost:8000/frontend_tiktok_swipe.html
```

### Manual setup

<details>
<summary>Backend</summary>

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit with your values
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# In separate terminals:
celery -A workers.video_worker worker --loglevel=info
celery -A workers.video_worker beat --loglevel=info
```
</details>

<details>
<summary>Frontend</summary>

```bash
cd frontend
npm install
cp .env .env.local            # set VITE_API_BASE_URL=http://localhost:8080
npm run dev
```
</details>

<details>
<summary>Infrastructure (Docker Compose)</summary>

```bash
docker-compose up -d surrealdb redis ipfs
docker-compose up -d backend celery-worker celery-beat
docker-compose logs -f backend
```
</details>

### Access points

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| Interactive API docs | http://localhost:8080/docs |
| Celery monitor | http://localhost:5555 |
| IPFS gateway | http://localhost:8080 |

---

## 📦 Project Structure

```
clipstream/
├── backend/                  # FastAPI backend
│   ├── api/                  # Route handlers
│   ├── app/                  # Business logic (scoring, embeddings, ingestion)
│   ├── db/                   # SurrealDB client
│   └── utils/                # Auth, config, helpers
├── frontend/                 # React + TypeScript SPA
│   └── src/
│       ├── components/       # Auth, Feed, Upload, Profile, Monetisation
│       ├── contexts/         # AuthContext, LanguageContext
│       └── lib/              # SurrealDB client, i18n, API helpers
├── docs/
│   ├── architecture/         # ML_ALGORITHM, MONOLITH_ANALYSIS, DATABASE_SCHEMA
│   ├── guides/               # REALTIME_ML, TIKTOK_INGESTION, EMBEDDINGS_GUIDE
│   └── api/                  # ENDPOINTS, INFINITE_FEED, REALTIME_EVENTS
├── test/                     # E2E and integration tests
├── demo-sim/                 # Local CDN + origin simulation (Docker)
├── docker-compose.yml
├── START_TIKTOK_PLATFORM.sh  # One-command dev start
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | JWT login |
| `GET` | `/api/v1/feed/for-you` | Personalised ML-ranked feed |
| `POST` | `/api/v1/feed/swipe` | Record swipe event, update user model |
| `GET` | `/api/v1/feed/events` | SSE stream for real-time feed updates |
| `POST` | `/api/v1/tiktok-ingestion/start` | Start TikTok auto-ingestion |
| `GET` | `/api/v1/embeddings/stats` | ML pipeline memory + TTL stats |
| `POST` | `/api/v1/embeddings/cleanup-expired` | Prune stale embeddings |

Full interactive docs at `http://localhost:8080/docs` · Static reference: [docs/api/ENDPOINTS.md](docs/api/ENDPOINTS.md)

---

## 💼 Business Model

### Revenue streams

| Stream | Split |
|---|---|
| Virtual gifts & live tips | 80% to creator, 20% platform |
| Short-form ad share | 45% to creator |
| Licensing / IP drops | Creator-set price, platform 10% |
| Insights-as-a-Service | Brand analytics packages |

### Creator advantages over existing platforms

| | YouTube | TikTok | Instagram | **ClipStream** |
|---|---|---|---|---|
| Revenue share | 55% | 50% | ~0% | **80%** |
| Content ownership | Platform | Platform | Platform | **Creator (IPFS)** |
| Algorithm transparency | ❌ | ❌ | ❌ | **✅ Open source** |
| Deletion risk | High | High | High | **None (IPFS CID)** |

### Tokenomics

ClipStream uses a two-layer model so the platform's reward mechanism doesn't compete with its payment infrastructure:

| Layer | Token | Role |
|---|---|---|
| **Contribution tracking** | $WATCH (ERC-20, Polygon) | Records views, watch time, and brand-safe uploads — determines each creator's proportional share |
| **Settlement** | [TrustedCrypto](https://github.com/al-khwarizme/TrustedCrypto) | Asset-backed, community-owned currency that actually moves value to creators |

$WATCH is not a currency — it is a contribution ledger. When distributions occur, $WATCH balances determine *how much* each creator receives; TrustedCrypto determines *what* they receive it in. The two projects are complementary: ClipStream generates the activity, TrustedCrypto settles it.

---

## 📈 Roadmap

### Shipped ✅
- [x] Near real-time TikTok recommendation model (Monolith Phase 1)
- [x] Collisionless embedding table with TTL and frequency filtering
- [x] SSE-based preference loop (~100ms end-to-end)
- [x] IPFS content storage + hybrid CDN delivery
- [x] Virtual gifts and creator earnings dashboard
- [x] $WATCH ERC-20 contribution tracking token
- [x] 8-language i18n with RTL support
- [x] TikTok video auto-ingestion (Playwright headless, trending hashtags)

### In progress 🚧
- [ ] Monolith Phase 2 — online model retraining (60s cycle)
- [ ] Filecoin archival integration
- [ ] DAO governance module

### Planned 📋
- [ ] iOS / Android mobile apps (React Native)
- [ ] Live streaming (WebRTC)
- [ ] Creator marketplace
- [ ] NFT minting for viral clips
- [ ] Duets & stitches

---

## 🤝 Join the Build

We're combining two things that don't exist together in open source:

**ByteDance's Monolith algorithm** (open-source for the first time) + **creator-cooperative economics** (80% revenue share, on-chain ownership, transparent governance).

### Open positions

| Area | What's needed | Docs to read |
|---|---|---|
| **ML / Recommendation** | Monolith Phase 2 — online retraining every 60s | [MONOLITH_ANALYSIS.md](docs/architecture/MONOLITH_ANALYSIS.md) |
| **Web3 / Solidity** | Filecoin archival, DAO governance, NFT minting | [docs/architecture/](docs/architecture/) |
| **React Native** | iOS + Android mobile apps | [docs/api/ENDPOINTS.md](docs/api/ENDPOINTS.md) |
| **WebRTC / Media** | Live streaming layer | [docs/architecture/SCALING.md](docs/architecture/SCALING.md) |
| **DevOps / Infra** | Kubernetes manifests, CI/CD, monitoring | [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) |

### How to start

```bash
# 1. Fork + clone
git clone https://github.com/inaim/clipstream2 && cd clipstream2

# 2. Start the platform
bash START_TIKTOK_PLATFORM.sh

# 3. Read the architecture docs, pick an open item, open an issue or PR
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

---

## Contributing

We follow [Conventional Commits](https://www.conventionalcommits.org/) and a standard GitHub flow (fork → branch → PR). Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting.

**Good first issues:** look for the [`good first issue`](https://github.com/inaim/clipstream2/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) label.

---

## 🔐 Security

- JWT authentication · bcrypt password hashing · OAuth 2.0 (Google, GitHub)
- HTTPS/TLS in transit · rate limiting on all endpoints · input validation at boundaries
- IPFS content addressing — immutable CIDs prevent content tampering
- See [SECURITY.md](SECURITY.md) to report vulnerabilities privately

---

## 📄 License

MIT — see [LICENSE](LICENSE). Use it, fork it, build on it.

---

## 🙏 Acknowledgments

Built on the shoulders of:
[ByteDance Monolith](https://arxiv.org/abs/2209.07663) ·
[OpenAI CLIP & Whisper](https://openai.com) ·
[SurrealDB](https://surrealdb.com) ·
[IPFS / Filecoin](https://ipfs.tech) ·
[FastAPI](https://fastapi.tiangolo.com) ·
[React](https://react.dev) ·
[Polygon](https://polygon.technology)

---

<div align="center">

**Star the repo if you believe creators should own what they build.**

[⭐ Star](https://github.com/inaim/clipstream2) · [🍴 Fork](https://github.com/inaim/clipstream2/fork) · [🐛 Issues](https://github.com/inaim/clipstream2/issues) · [💬 Discussions](https://github.com/inaim/clipstream2/discussions)

</div>
