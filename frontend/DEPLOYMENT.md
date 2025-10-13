# Production Deployment Guide

## Overview
ClipStream is configured for deployment with:
- **Frontend**: `clipstream.finailabz.com` (Static hosting - Netlify/Vercel)
- **Backend**: `backend.finailabz.com` (FastAPI server)

## Frontend Deployment (Netlify/Vercel)

Note: See `.env.example` for a template of environment variables required by both frontend and backend, including OAuth provider placeholders.


### 1. Environment Configuration
For production builds, use the production environment variables:

```bash
# Copy production config
cp .env.production .env

# Or set environment variables in your hosting platform:
VITE_API_BASE_URL=https://backend.finailabz.com
```

### 2. Build and Deploy
```bash
# Install dependencies
yarn install

# Build for production
yarn build

# Deploy the dist/ folder to your hosting platform
```

### 3. Netlify Configuration
Create `netlify.toml` in the root directory:
```toml
[build]
  publish = "dist"
  command = "yarn build"

[build.environment]
  VITE_API_BASE_URL = "https://backend.finailabz.com"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## Backend Deployment

### 1. Server Requirements
- Python 3.9+
- Redis server
- MongoDB (optional for Phase 1)

### 2. Installation
```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
# Backend configuration
export ALLOWED_ORIGINS="https://clipstream.finailabz.com"
export MONGO_DB_URL="mongodb://localhost:27017/video_platform"
export REDIS_HOST="redis://localhost:6379"
```

### 4. OAuth Provider Configuration (Google & Facebook examples)
Set the OAuth client IDs/secrets in your environment. If these are present, the backend will perform real OAuth flows; otherwise it falls back to the dev mock flow.

Required environment variables:

```bash
# Frontend/Backend URLs
export BACKEND_BASE_URL="https://backend.finailabz.com"
export FRONTEND_BASE_URL="https://clipstream.finailabz.com"

# Google (OpenID Connect)
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"

# Facebook
export FACEBOOK_CLIENT_ID="your-facebook-client-id"
export FACEBOOK_CLIENT_SECRET="your-facebook-client-secret"

# (Optional) Apple/Twitter credentials if you configure them
export APPLE_CLIENT_ID="..."
export APPLE_CLIENT_SECRET="..."
```

Google setup quick steps:
- Go to Google Cloud Console → APIs & Services → Credentials
- Create OAuth 2.0 Client IDs (Web application)
- Authorized redirect URIs: `https://backend.finailabz.com/api/v1/auth/callback`
- Add the client ID/secret to the environment

Facebook setup quick steps:
- Go to Facebook Developers → My Apps → Add a New App
- Add Facebook Login, configure Valid OAuth Redirect URIs: `https://backend.finailabz.com/api/v1/auth/callback`
- Set client ID/secret in environment

Important: For production, ensure your backend is served over HTTPS and the redirect URIs match exactly the values configured in the provider consoles.

### 4. Run Production Server
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000

# Or using gunicorn for production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 5. Background Tasks (Optional)
Start Celery workers for background processing:
```bash
celery -A celery_app worker --loglevel=info
```

## Testing Production Setup Locally

### 1. Test with production URLs locally:
```bash
# Update .env to use production backend
echo "VITE_API_BASE_URL=https://backend.finailabz.com" > .env

# Build and serve locally
yarn build
yarn preview
```

### 2. Test backend CORS:
```bash
curl -X OPTIONS https://backend.finailabz.com/api/v1/auth/register \
  -H "Origin: https://clipstream.finailabz.com" \
  -H "Access-Control-Request-Method: POST"
```

## Deployment Checklist

### Frontend (clipstream.finailabz.com):
- [ ] Environment variables configured
- [ ] Build succeeds with production config
- [ ] Routing/redirects configured for SPA
- [ ] HTTPS enabled

### Backend (backend.finailabz.com):
- [ ] CORS allows clipstream.finailabz.com origin
- [ ] API endpoints accessible
- [ ] Database connections configured
- [ ] Background tasks running (if needed)
- [ ] HTTPS enabled
- [ ] Health check endpoint working

## Health Checks

### Frontend Health Check:
- Visit `https://clipstream.finailabz.com`
- Verify app loads and auth buttons work

### Backend Health Check:
- Visit `https://backend.finailabz.com/docs`
- Test API endpoint: `https://backend.finailabz.com/api/v1/feed/for-you?user_id=test`

## Troubleshooting

### CORS Issues:
- Verify backend CORS includes frontend domain
- Check browser network tab for preflight requests
- Ensure both domains use HTTPS

### API Connection Issues:
- Verify `VITE_API_BASE_URL` environment variable
- Check network tab for 404/500 errors
- Test backend endpoints directly

### Build Issues:
- Clear node_modules and reinstall: `rm -rf node_modules && yarn install`
- Clear Vite cache: `yarn vite --force`
- Check environment variable naming (must start with `VITE_`)