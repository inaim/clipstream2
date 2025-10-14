Clipostream — Beta Scope & Implementation Plan

Version: 2025-10-14
Author: scoped by dev team

Overview
--------
This document scopes a practical Beta (v0.1) of Clipostream that demonstrates the platform's core value-propositions without building the full production system. The Beta focuses on: uploads, playback (HLS), creator profiles, simple economics accounting, archival simulation (IPFS-like), recommendation stubs, auth, and a caching CDN simulation (already implemented in demo-sim).

Primary goals
-------------
- Demonstrate upload → processing (stubbed) → playback via CDN with cache behaviors.
- Provide minimal creator UX: profile, upload history, playback, and a simple earnings ledger.
- Simulate cold archival storage (IPFS simulation) and show retrieval latency differences.
- Provide reproducible infra that can run locally using Docker Compose for testing and demos.

Success criteria
----------------
- A user can sign up, upload a video file (or sample), and play it via an HLS-capable player served through the CDN proxy.
- The platform shows fast playback for cached content and slower retrieval for cold archived content (simulated), and subsequently serves cached content quickly (MISS→HIT).
- Creator receives a simple accounting entry for each view (off-chain ledger) and can view a basic balance in the UI.
- Basic survivability: services run in Docker Compose, with health checks and documented run steps.

MVP Feature set (concrete)
---------------------------
1. Auth & Users
   - JWT-based authentication (email+password), signup/login, token refresh.
   - Creator profile with display name, bio, and basic settings.

2. Upload & Storage (simulation)
   - Upload endpoint accepts a small video file (or uses sample files) and stores file locally under `/storage/origin/<id>/`.
   - Generate an internal content hash (SHA-256) and return as `content_hash` (simulates IPFS CID).
   - Mark uploaded content as HOT initially and schedule archival to "IPFS-sim" after 30s (manifest only).

3. Processing (stubs)
   - Transcoding is stubbed: generate HLS manifest and a few small sample segments (or symlink sample segments) so player can play.
   - Run a simple transcription/embedding stub that returns deterministic values.

4. Playback & CDN
   - Serve HLS manifest and segments from `origin` (nginx) behind the `cdn` caching proxy (demo-sim).
   - CDN caches segments and API responses; the demo already implements cache behavior for JSON endpoints. Extend to static HLS segments.

5. Ledger & Analytics
   - Record views: simple rule (count a view after 3s of playback via client event). Write to SurrealDB (or for Beta, a simple JSON/SQLite store).
   - Add a simple earnings calculation: e.g., 1 microtoken per view; track ledger entries in DB and expose balance.

6. Admin / Dev Utilities
   - Simple admin endpoint to list content, purge cache (via header or endpoint), and force archival.

Non-MVP (deferred)
-------------------
- Real IPFS/Filecoin integration and on-chain minting
- Production transcoding cluster, AI model training, multi-region CDN
- Payments routing and KYC flows (design only in Beta)

Data model (high-level)
-----------------------
- users
  - id, email, hashed_password, display_name, is_creator, created_at
- videos
  - id, owner_id, title, description, content_hash, status (hot/archived), created_at, hls_manifest_path
- views
  - id, video_id, user_id (nullable), started_at, duration, counted_at
- ledger_entries
  - id, user_id, amount, reason, reference_id, created_at

SurrealDB vs SQLite
-------------------
- For Beta, start with SQLite (fast to iterate) and provide SurrealDB schema + migration scripts for the next milestone. Implement DB access via a small repository layer so switching is straightforward.

Infra & architecture (local dev)
--------------------------------
- docker-compose (compose v3.8) with services:
  - origin (nginx serving static/HLS files)
  - backend (FastAPI for APIs & upload handler)
  - cdn (nginx caching reverse-proxy) — demo-sim already wired
  - storage volume mounted to `./storage` for uploaded files
  - db (SQLite file or SurrealDB container optional)

APIs (sketch)
-------------
- POST /api/v1/auth/signup {email,password,display_name}
- POST /api/v1/auth/login {email,password} -> {access_token}
- POST /api/v1/upload -> multipart form; returns {video_id, content_hash, hls_manifest}
- GET /api/v1/videos/{id} -> metadata
- POST /api/v1/views {video_id, duration} -> records a view (client calls after 3s)
- POST /api/v1/admin/purge?path=... -> instruct CDN to bypass or purge

Processing & HLS
----------------
- For Beta, implement a minimal HLS generator:
  - Accept uploaded file and copy/convert to small pre-generated segments OR use ffmpeg if available in container to create segments.
  - Store manifest at `/origin/content/<id>/index.m3u8` and segments in same folder.

Recommendation engine (stub)
----------------------------
- Return simple chronological or trending list based on view counts. Provide a deterministic stubbed endpoint that returns related videos using simple heuristics.

Security & rate-limiting
------------------------
- JWT tokens for API auth
- Rate-limit uploads and API endpoints using simple in-memory counters for Beta
- Ensure file uploads are validated (size, mime type)

Observability
-------------
- Basic logging to stdout (structured JSON optional)
- Health endpoints: /health and /ready
- Add `X-Cache-Status` and `X-Cache-TTL` headers on origin responses for debugging (already present)

Milestones & timeline (rough)
-----------------------------
Assume a small engineering team (1-2 devs). Times are rough estimates.

Milestone 0 — Prep & Demo-sim polish (1 week)
- Finalize demo-sim (done)
- Add slow/cold endpoint & test script (done)
- Acceptance: run demo and verify MISS→HIT

Milestone 1 — Core backend + auth + local storage (2 weeks)
- Implement FastAPI backend with auth, upload endpoint, storage layout
- Implement SQLite repo layer
- Acceptance: sign up, upload sample video, data persisted

Milestone 2 — HLS generation & origin hosting (2 weeks)
- Add HLS generation (ffmpeg or sample segments)
- Serve manifest/segments from origin nginx
- Acceptance: play a video through CDN proxy

Milestone 3 — Views ledger & simple earnings (1 week)
- Implement view recording and simple microtoken ledger
- Acceptance: views increment ledger and appear in creator dashboard

Milestone 4 — Archival simulation & admin tools (1 week)
- Add archival scheduler (marks content archived, simulates slow retrieval)
- Admin purge endpoint to bypass CDN
- Acceptance: content moves HOT→ARCHIVED and retrieval shows latency

Milestone 5 — Frontend minimal UI (2 weeks)
- Basic React frontend: signup/login, upload form, creator profile, video player
- Integrate with auth and APIs
- Acceptance: end-to-end flow from signup→upload→play→ledger

Milestone 6 — Hardening, docs & Beta release (1 week)
- Health checks, README, runbook, basic CI, security review
- Acceptance: documented Beta release steps + example demo

Total estimated: ~9 weeks (single dev) — compressible with more engineers.

Risks & mitigations
-------------------
- Video transcoding complexity: use pre-generated segments or ffmpeg in a single container to reduce complexity.
- Storage growth: for Beta keep small sample files and purge old uploads; use local disk.
- Security: Beta is not production — warn about keys and secrets in README.
- IPFS / on-chain costs: simulate archival for Beta; plan integration separately with clear boundaries.

Deliverables
------------
- Repo additions: `backend/` (FastAPI), `frontend/` (React minimal), `storage/`, `docker-compose.beta.yml`, `migrations/` or `schema/` files for DB.
- Documentation: `SCOPING_BETA.md`, `demo-sim/README.md`, `beta-runbook.md` with step-by-step deploy.
- Tests: simple integration tests for upload→playback and view counting.

Immediate next actions (this sprint)
-----------------------------------
1. Kick off Milestone 1: scaffold backend repo structure and implement auth & SQLite repository layer. (create files, skeleton endpoints)
2. Wire upload endpoints and local storage layout; add health endpoints.
3. Add simple integration tests and update README with run steps.

If you want, I can start Milestone 1 now: create the FastAPI scaffold under `backend-beta/` with auth endpoints, SQLite repo, and health checks. This will include:
- `backend-beta/main.py` (FastAPI app)
- `backend-beta/requirements.txt`
- `backend-beta/Dockerfile`
- a minimal `backend-beta/app/auth.py` and `app/repos.py` using `sqlite3` or `databases` library

Please confirm and I will scaffold the backend-beta folder and implement the first endpoints.
