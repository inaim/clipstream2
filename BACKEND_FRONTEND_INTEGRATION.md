# 🔗 ClipStream Backend-Frontend Integration Guide

Complete guide for integrating the ClipStream frontend with the backend API.

## 📋 Overview

The ClipStream application consists of:
- **Backend**: FastAPI application with SurrealDB Cloud
- **Frontend**: React + Vite application
- **Deployment**: Google Cloud Run (backend) + Cloud Storage/CDN (frontend)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  (React + Vite + TypeScript)                                │
│  - Hosted on Cloud Storage + CDN                            │
│  - URL: https://clipstream.finailabz.com                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│  (FastAPI + Python)                                         │
│  - Hosted on Google Cloud Run                               │
│  - URL: https://backend.finailabz.com                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (wss://)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      SurrealDB Cloud                         │
│  - Multi-model database                                     │
│  - Region: AWS Europe (Ireland)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Setup

### 1. Environment Variables

Create `backend/.env` with:

```bash
# Application
APP_ENV=development
SECRET_KEY=your-secret-key-min-32-chars-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SurrealDB Cloud
SURREALDB_URL=wss://ancient-valley-06cu6ilhgptbp4ttr1a04b77oc.aws-euw1.surreal.cloud
SURREALDB_USER=root
SURREALDB_PASS=your-password
SURREALDB_NS=clipstream
SURREALDB_DB=production

# URLs
FRONTEND_BASE_URL=http://localhost:5173
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# OAuth (Google)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Optional
REDIS_URL=redis://localhost:6379/0
ENABLE_IPFS=false
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run Backend Locally

```bash
cd backend
python main.py
```

Backend will be available at: `http://localhost:8080`

### 4. Test Backend Health

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "surrealdb": "connected"
}
```

---

## 🌐 Frontend Setup

### 1. Environment Variables

Create `frontend/.env.development` with:

```bash
VITE_API_BASE_URL=http://localhost:8080
VITE_BACKEND_URL=http://localhost:8080
```

Create `frontend/.env.production` with:

```bash
VITE_API_BASE_URL=https://clipstream-backend.finailabz.com
VITE_BACKEND_URL=https://clipstream-backend.finailabz.com
```

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Run Frontend Locally

```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 4. Build for Production

```bash
cd frontend
npm run build
```

---

## 📡 API Endpoints

### Authentication

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "display_name": "John Doe"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "user:abc123"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "user:abc123"
}
```

#### Get User Profile
```http
GET /api/v1/users/{user_id}
Authorization: Bearer {access_token}
```

Response:
```json
{
  "user_id": "user:abc123",
  "email": "user@example.com",
  "display_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Video Upload

#### Upload Video
```http
POST /api/upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: <video file>
title: "My Video"
```

Response:
```json
{
  "video_id": "video:xyz789",
  "playback_url": "/uploads/1234567890_abc.mp4",
  "title": "My Video",
  "status": "success",
  "message": "Video uploaded successfully"
}
```

### Feed

#### Get For You Feed
```http
GET /api/v1/feed/for-you?limit=20&offset=0
Authorization: Bearer {access_token}
```

Response:
```json
{
  "items": [
    {
      "id": "video:xyz789",
      "title": "My Video",
      "video_url": "/uploads/1234567890_abc.mp4",
      "owner": {
        "user_id": "user:abc123",
        "display_name": "John Doe"
      },
      "views_count": 100,
      "likes_count": 10,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### Get Following Feed
```http
GET /api/v1/feed/following?user_id={user_id}&limit=20&offset=0
Authorization: Bearer {access_token}
```

### Social

#### Like Video
```http
POST /api/likes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "user_id": "user:abc123",
  "video_id": "video:xyz789"
}
```

#### Follow User
```http
POST /api/follows
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "follower_id": "user:abc123",
  "following_id": "user:def456"
}
```

---

## 🔐 Authentication Flow

### 1. Frontend Login Flow

```typescript
import { authApi } from './services/api';

// Login
const { access_token, user_id } = await authApi.login(email, password);

// Store token
localStorage.setItem('access_token', access_token);
localStorage.setItem('user_id', user_id);

// Get user profile
const profile = await authApi.getProfile(user_id);
```

### 2. Backend Token Validation

The backend validates JWT tokens using the `get_current_user` dependency:

```python
from fastapi import Depends
from utils.auth import get_current_user

@router.get("/protected")
async def protected_route(current_user_id: str = Depends(get_current_user)):
    return {"user_id": current_user_id}
```

### 3. OAuth Flow (Google)

1. Frontend redirects to: `GET /api/v1/auth/google`
2. User authenticates with Google
3. Google redirects to: `GET /api/v1/auth/google/callback`
4. Backend creates/finds user and redirects to frontend with token
5. Frontend stores token and fetches user profile

---

## 📦 Frontend API Service

The frontend uses a centralized API service located at `frontend/src/services/api.ts`:

```typescript
import api from './services/api';

// Upload video
const result = await api.uploadViaBackend(file, title);

// Get feed
const feed = await api.feed.getForYouFeed(userId);

// Like video
await api.social.likeVideo(userId, videoId);
```

---

## 🚀 Deployment

### Backend to Cloud Run

```bash
cd backend

# Build and deploy
gcloud run deploy clipstream-backend \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=production" \
  --set-env-vars="SURREALDB_URL=wss://..." \
  --set-secrets="SURREALDB_PASS=surrealdb-password:latest"
```

### Frontend to Cloud Storage

```bash
cd frontend

# Build
VITE_API_BASE_URL=https://backend.finailabz.com npm run build

# Deploy
gsutil -m rsync -r -d dist/ gs://clipstream-frontend/
```

---

## 🔍 Testing

### Test Backend Locally

```bash
# Health check
curl http://localhost:8080/health

# Register user
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Test Frontend Locally

1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:5173`
4. Test registration, login, and video upload

---

## 🐛 Troubleshooting

### CORS Errors

**Problem**: Frontend can't connect to backend

**Solution**: 
1. Check `ALLOWED_ORIGINS` in backend `.env`
2. Ensure frontend URL is included
3. Restart backend

### Authentication Errors

**Problem**: "Could not validate credentials"

**Solution**:
1. Check token is stored in localStorage
2. Verify token is sent in Authorization header
3. Check SECRET_KEY matches between requests

### Upload Errors

**Problem**: Video upload fails

**Solution**:
1. Check `uploads/` directory exists in backend
2. Verify file size limits
3. Check backend logs for errors

### Database Connection Errors

**Problem**: "SurrealDB connection failed"

**Solution**:
1. Verify SURREALDB_URL is correct
2. Check credentials (user/pass)
3. Ensure namespace and database exist
4. Check network connectivity

---

## 📊 Monitoring

### Backend Logs

```bash
# Local
tail -f backend/logs/app.log

# Cloud Run
gcloud run services logs read clipstream-backend --region europe-west1
```

### Frontend Errors

Check browser console for errors:
- Network errors (API calls)
- Authentication errors
- Upload errors

---

## ✅ Integration Checklist

### Backend
- [x] FastAPI app created with proper structure
- [x] SurrealDB client configured
- [x] Authentication endpoints working
- [x] Video upload endpoint working
- [x] Feed endpoints working
- [x] CORS configured for frontend
- [x] Health check endpoint
- [x] Environment variables configured

### Frontend
- [x] API service created (`services/api.ts`)
- [x] Authentication flow implemented
- [x] Video upload component updated
- [x] Feed components using API
- [x] Environment variables configured
- [x] Build process working

### Deployment
- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Cloud Storage
- [ ] Custom domains configured
- [ ] SSL certificates configured
- [ ] Environment variables set in production
- [ ] Monitoring and logging configured

---

## 🎉 Summary

Your ClipStream application is now fully integrated:

1. **Backend** (`backend/main.py`):
   - ✅ FastAPI with SurrealDB Cloud
   - ✅ Authentication (email/password + OAuth)
   - ✅ Video upload and storage
   - ✅ Feed endpoints
   - ✅ Social features (likes, follows)
   - ✅ Ready for Cloud Run deployment

2. **Frontend** (`frontend/src/services/api.ts`):
   - ✅ Centralized API service
   - ✅ Authentication integration
   - ✅ Video upload integration
   - ✅ Feed integration
   - ✅ Ready for production build

3. **Deployment**:
   - ✅ Dockerfile for Cloud Run
   - ✅ Environment configuration
   - ✅ Deployment guide created
   - ✅ Ready to deploy!

**Next Steps**:
1. Test locally: Start backend and frontend
2. Deploy backend to Cloud Run
3. Deploy frontend to Cloud Storage
4. Configure custom domains
5. Test production deployment

🚀 **Your application is ready for Cloud Run!**

