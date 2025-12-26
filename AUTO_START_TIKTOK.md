# TikTok Auto-Ingestion - Auto-Start on App Launch

## ✅ Changes Made

I've updated the backend to **automatically start TikTok video scraping** when the app launches!

### Modified File:
- `backend/main.py` - Updated startup lifecycle

### What Changed:

1. **Default enabled** - Changed from `ENABLE_TIKTOK_AUTO_INGEST=false` to `ENABLE_TIKTOK_AUTO_INGEST=true`
2. **Enhanced logging** - Better startup messages showing scraping configuration
3. **Automatic browser scraping** - Uses Playwright by default with infinite scroll

## 🚀 How It Works Now

When you start your backend:

```bash
cd ~/Documents/projects/clipstream/backend
python main.py
```

You'll see in the startup logs:

```
[STEP 3.5] Starting TikTok auto-ingestion with browser scraping...
✅ TikTok auto-ingestion service started (browser scraping enabled)
   - Scraping trending hashtags every 5 minutes
   - Browser: Headless Chromium with infinite scroll
   - Sources: #fyp, #viral, #trending, etc.
```

The service will:
- ✅ Start automatically on app launch
- ✅ Scrape trending hashtags every 5 minutes
- ✅ Use headless browser with infinite scroll
- ✅ Download videos and ingest them into your database
- ✅ Make videos available in your feeds immediately

## 📋 Prerequisites

Make sure you have Playwright installed:

```bash
cd ~/Documents/projects/clipstream/backend
pip install playwright yt-dlp
playwright install chromium
```

## 🎛️ Configuration

### Option 1: Keep Default (Recommended)

Do nothing! Auto-ingestion starts automatically with:
- **Interval**: Every 5 minutes
- **Videos per cycle**: 10 videos
- **Browser scraping**: Enabled
- **Hashtags**: #fyp, #viral, #trending, etc.

### Option 2: Disable Auto-Start

Add to your `.env` file:

```bash
ENABLE_TIKTOK_AUTO_INGEST=false
```

Then start manually via API when needed:

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"use_browser": true, "videos_per_fetch": 20}' | jq
```

### Option 3: Custom Configuration

Start the app, then reconfigure via API:

```bash
# Stop current instance
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq

# Start with custom config
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "fetch_interval": 180,
    "videos_per_fetch": 30
  }' | jq
```

## 🔍 Monitoring

### Check Status

```bash
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

Response:
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "use_browser": true,
    "fetch_interval": 300,
    "videos_per_fetch": 10,
    "total_fetched": 45,
    "total_ingested": 42,
    "total_failed": 3,
    "success_rate": 0.933,
    "last_fetch_time": 1703012345.67
  }
}
```

### Trigger Manual Fetch

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq
```

### Stop Service

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq
```

## 📊 What Gets Scraped

By default, the service scrapes these trending hashtags:
- #fyp (For You Page)
- #foryou
- #viral
- #trending
- #funny
- #comedy
- #sports
- #music
- #gaming
- #dance
- #cooking
- #travel

Each cycle fetches videos from multiple hashtags for diversity.

## 🔄 Workflow

```
App Starts
    ↓
TikTok Auto-Ingestion Starts
    ↓
Every 5 Minutes:
    ↓
Browser launches → Navigates to hashtag feeds → Infinite scroll
    ↓
Extracts video URLs + metadata
    ↓
Downloads videos with yt-dlp
    ↓
Ingests into SurrealDB
    ↓
Videos appear in /api/v1/feed/for-you
    ↓
Repeat...
```

## 🛠️ Troubleshooting

### Issue: Service doesn't start

**Error in logs:**
```
⚠️  Failed to start TikTok auto-ingestion: BrowserType.launch: Executable doesn't exist
```

**Solution:**
```bash
playwright install chromium
```

### Issue: Videos not appearing in feed

**Check status:**
```bash
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

Look for `success_rate`. If it's 0, check:
1. Playwright installed? `playwright install chromium`
2. Internet connection working?
3. Check backend logs for errors

### Issue: Want to disable auto-start

Add to `.env`:
```bash
ENABLE_TIKTOK_AUTO_INGEST=false
```

Restart the backend.

## 📝 Next Steps

1. **Copy changes to main repository:**
   ```bash
   cp ~/.claude-worktrees/clipstream/cool-knuth/backend/main.py ~/Documents/projects/clipstream/backend/
   ```

2. **Install Playwright:**
   ```bash
   cd ~/Documents/projects/clipstream/backend
   playwright install chromium
   ```

3. **Restart backend:**
   ```bash
   python main.py
   ```

4. **Watch the magic happen!**
   Videos will start appearing in your feeds automatically every 5 minutes.

## 🎉 Result

Now when you start your app, TikTok video scraping starts automatically. No manual API calls needed!

Your platform will continuously pull fresh viral content from TikTok and make it available to your users. 🚀
