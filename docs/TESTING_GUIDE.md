# 🧪 ClipStream Testing Guide

Complete guide for testing the ClipStream backend and frontend.

---

## 🚀 Quick Start

### Test Backend Connection

```bash
# From project root
./run-test.sh

# OR manually
python3 test/test_backend_connection.py
```

This will test:
1. ✅ SurrealDB connection
2. ✅ Authentication
3. ✅ Query execution
4. ✅ Backend db_client

---

## 🔧 Setup for Testing

### 1. Install Backend Dependencies

```bash
cd backend

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Make sure `backend/.env` exists with:

```bash
# SurrealDB Cloud
SURREALDB_URL=wss://ancient-valley-06cu6ilhgptbp4ttr1a04b77oc.aws-euw1.surreal.cloud
SURREALDB_USER=root
SURREALDB_PASS=your-password
SURREALDB_NS=clipstream
SURREALDB_DB=production

# Application
SECRET_KEY=your-secret-key-min-32-chars
APP_ENV=development

# URLs
BACKEND_BASE_URL=http://localhost:8080
FRONTEND_BASE_URL=http://localhost:5173
```

---

## 🧪 Running Tests

### Backend Connection Test

```bash
# Run the test script
./run-test.sh

# Expected output:
# ✅ Successfully imported settings
# ✅ Successfully imported Surreal
# ✅ Connection initialized
# ✅ Namespace and database selected
# ✅ Successfully signed in
# ✅ Query successful
# ✅ ALL TESTS PASSED!
```

### Manual Backend Test

```bash
cd backend
source venv/bin/activate
python3 main.py
```

Then in another terminal:

```bash
# Test health endpoint
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","surrealdb":"connected"}

# Test root endpoint
curl http://localhost:8080/

# Test API docs
open http://localhost:8080/docs
```

### Frontend Test

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Open browser
open http://localhost:5173
```

---

## 📋 Test Checklist

### Backend Tests

- [ ] **Connection Test**
  ```bash
  ./run-test.sh
  ```

- [ ] **Health Check**
  ```bash
  curl http://localhost:8080/health
  ```

- [ ] **API Documentation**
  ```bash
  open http://localhost:8080/docs
  ```

- [ ] **User Registration**
  ```bash
  curl -X POST http://localhost:8080/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123","display_name":"Test User"}'
  ```

- [ ] **User Login**
  ```bash
  curl -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test123"}'
  ```

- [ ] **Get User Profile** (requires token from login)
  ```bash
  curl http://localhost:8080/api/v1/users/user:123 \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

### Frontend Tests

- [ ] **Build Test**
  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Type Check**
  ```bash
  cd frontend
  npm run typecheck
  ```

- [ ] **Lint Check**
  ```bash
  cd frontend
  npm run lint
  ```

### Integration Tests

- [ ] **Login Flow**
  1. Start backend: `cd backend && python3 main.py`
  2. Start frontend: `cd frontend && npm run dev`
  3. Open http://localhost:5173
  4. Click "Sign Up" or "Log In"
  5. Enter credentials
  6. Verify redirect to dashboard

- [ ] **Video Upload**
  1. Login to application
  2. Click upload button
  3. Select video file
  4. Enter title
  5. Submit
  6. Verify video appears in feed

- [ ] **Social Features**
  1. Like a video
  2. Follow a user
  3. Post a comment
  4. Verify counts update

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'utils'"

**Problem**: Python can't find backend modules

**Solution**: The test script should handle this automatically, but if you're running Python directly:

```python
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Now import
from utils.config import settings
```

### "ModuleNotFoundError: No module named 'surrealdb'"

**Problem**: SurrealDB package not installed

**Solution**:
```bash
cd backend
source venv/bin/activate
pip install surrealdb
```

### "Connection refused" or "Connection failed"

**Problem**: Can't connect to SurrealDB Cloud

**Solutions**:
1. Check internet connection
2. Verify SURREALDB_URL is correct
3. Check credentials (user/pass)
4. Verify namespace and database exist

### "CORS error" in browser

**Problem**: Frontend can't connect to backend

**Solution**: Check CORS configuration in `backend/main.py`:
```python
allow_origins=settings.ALLOWED_ORIGINS + [
    "http://localhost:5173",
    "http://localhost:3000"
]
```

### "401 Unauthorized"

**Problem**: Missing or invalid auth token

**Solution**:
1. Login first to get token
2. Check token is stored in localStorage
3. Verify token is sent in Authorization header

---

## 📊 Test Coverage

### Backend Endpoints

| Endpoint | Method | Test Status |
|----------|--------|-------------|
| `/health` | GET | ✅ Automated |
| `/` | GET | ✅ Automated |
| `/api/v1/auth/register` | POST | ⚠️ Manual |
| `/api/v1/auth/login` | POST | ⚠️ Manual |
| `/api/v1/users/{id}` | GET | ⚠️ Manual |
| `/api/upload` | POST | ⚠️ Manual |
| `/api/videos` | GET | ⚠️ Manual |
| `/api/likes` | POST/DELETE | ⚠️ Manual |
| `/api/follows` | POST/DELETE | ⚠️ Manual |
| `/api/comments` | GET/POST | ⚠️ Manual |

### Frontend Components

| Component | Test Status |
|-----------|-------------|
| Authentication | ⚠️ Manual |
| Profile Page | ⚠️ Manual |
| Video Feed | ⚠️ Manual |
| Video Upload | ⚠️ Manual |
| Comments | ⚠️ Manual |
| Likes/Follows | ⚠️ Manual |

---

## 🔄 Continuous Testing

### Watch Mode (Backend)

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
python3 main.py
# Server will restart on file changes
```

### Watch Mode (Frontend)

```bash
cd frontend

# Dev server with hot reload
npm run dev
# Browser will auto-refresh on changes
```

---

## 📝 Writing New Tests

### Backend Test Template

```python
import sys
from pathlib import Path

# Setup path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
from utils.config import settings
from db.surrealdb_client import db_client

async def test_my_feature():
    """Test description"""
    try:
        await db_client.connect()
        
        # Your test code here
        result = await db_client.some_method()
        
        assert result is not None, "Result should not be None"
        print("✅ Test passed")
        
        await db_client.disconnect()
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_my_feature())
    sys.exit(0 if result else 1)
```

### Frontend Test Template

```typescript
import { describe, it, expect } from 'vitest';
import { profileApi } from '../services/surrealdb';

describe('Profile API', () => {
  it('should get user profile', async () => {
    const profile = await profileApi.getProfile('user:123');
    expect(profile).toBeDefined();
    expect(profile.user_id).toBe('user:123');
  });
});
```

---

## 🎯 Test Scenarios

### Scenario 1: New User Registration

1. Open frontend
2. Click "Sign Up"
3. Enter email, password, display name
4. Submit form
5. **Expected**: Redirect to dashboard, user logged in

### Scenario 2: Video Upload and View

1. Login as user
2. Click upload button
3. Select video file
4. Enter title
5. Submit
6. **Expected**: Video appears in feed
7. Click video to play
8. **Expected**: Video plays, view count increases

### Scenario 3: Social Interaction

1. Login as User A
2. View User B's profile
3. Click follow button
4. **Expected**: Following count increases
5. Like one of User B's videos
6. **Expected**: Like count increases
7. Post a comment
8. **Expected**: Comment appears in list

---

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8080/docs
- **Backend Integration Guide**: `BACKEND_FRONTEND_INTEGRATION.md`
- **Mobile API Guide**: `FRONTEND_MOBILE_API_GUIDE.md`
- **Deployment Guide**: `CLOUD_RUN_DEPLOYMENT.md`

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Integration tests pass
- [ ] No console errors in browser
- [ ] No errors in backend logs
- [ ] Environment variables configured
- [ ] CORS configured correctly
- [ ] Authentication working
- [ ] Video upload working
- [ ] Social features working
- [ ] Mobile responsive
- [ ] Performance acceptable

---

**Happy Testing! 🎉**

