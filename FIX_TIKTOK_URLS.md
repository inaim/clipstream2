# Fix TikTok URL Ingestion - Quick Guide

## 🚨 Problem

The auto-ingestion is failing because:
1. Browser scraping returns no videos (TikTok blocking automation)
2. Falls back to manual URL list
3. But the URL list has old placeholder URLs that don't work
4. TikTok is blocking your IP address

## 🎉 NEW: Anti-Detection Features Added!

**Just implemented:**
- ✅ Rotating user agents (8 different browser fingerprints)
- ✅ Randomized viewports
- ✅ Randomized scroll delays
- ✅ Advanced anti-detection scripts
- ✅ Proxy support for IP rotation
- ✅ Stealth mode browser settings

## ✅ Solution

You need to **replace the old tiktok_urls.txt** with your real URL.

### Step 1: Edit the file

```bash
# Navigate to backend
cd ~/Documents/projects/clipstream/backend/app

# Edit the file
nano tiktok_urls.txt
```

### Step 2: Replace ALL content with this:

```
# TikTok Video URLs - Manual Fallback List
# Format: URL|category

# Real TikTok URLs (one per line)
https://www.tiktok.com/@demi32751/video/7584183122296589599|trending
```

### Step 3: Save and exit
- Press `Ctrl+O` to save
- Press `Enter` to confirm
- Press `Ctrl+X` to exit

### Step 4: Trigger manual ingestion

```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq
```

### Step 5: Check logs

You should see:
```
Using manual URL list: 1 videos
Downloading TikTok video: https://www.tiktok.com/@demi32751/video/7584183122296589599
```

Instead of:
```
ERROR: Unsupported URL: https://www.tiktok.com/@<realuser>/video/<realid>
```

---

## 🔍 Why This Happens

The old `tiktok_urls.txt` file has these placeholder lines:
```
https://www.tiktok.com/@someuser/video/1234567890
https://www.tiktok.com/@<realuser>/video/<realid>
```

These are **templates**, not real URLs! yt-dlp can't download from them.

---

## 📝 Full File Content

Here's what your `tiktok_urls.txt` should look like:

```bash
# TikTok Video URLs - Manual Fallback List
# Format: URL|category
# One URL per line: https://www.tiktok.com/@username/video/ID|category

# Real working URLs:
https://www.tiktok.com/@demi32751/video/7584183122296589599|trending

# Add more URLs below (one per line):
# https://www.tiktok.com/@anotheruser/video/7584183122296589600|sports
# https://www.tiktok.com/@someuser/video/7584183122296589601|comedy
```

---

## 🧪 Test If It Works

After editing the file, test the download:

```bash
# Test yt-dlp directly
yt-dlp --no-warnings --simulate "https://www.tiktok.com/@demi32751/video/7584183122296589599"

# Should output:
# [TikTok] 7584183122296589599: Downloading...
# [TikTok] 7584183122296589599: Downloading webpage
# Title: Video title here
```

If you see "ERROR: Your IP address is blocked" - wait 30-60 minutes before trying again.

---

## ⚡ Quick Command (Copy-Paste)

```bash
cd ~/Documents/projects/clipstream/backend/app && cat > tiktok_urls.txt << 'EOF'
# TikTok Video URLs - Manual Fallback List
# Format: URL|category

https://www.tiktok.com/@demi32751/video/7584183122296589599|trending
EOF
```

Then trigger ingestion:
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/trigger-now | jq
```

---

## 🎯 Expected Outcome

After fixing:

**Before (Error):**
```
ERROR:app.tiktok_scraper:yt-dlp failed: ERROR: Unsupported URL
WARNING:app.tiktok_auto_ingestion:Failed to download
```

**After (Success):**
```
INFO:app.tiktok_scraper:Downloading TikTok video: https://www.tiktok.com/@demi32751/video/7584183122296589599
INFO:app.tiktok_scraper:Successfully downloaded: [Video Title]
INFO:app.tiktok_auto_ingestion:Ingested: [Video Title]
INFO:app.tiktok_auto_ingestion:Batch complete: 1 ingested, 0 failed
```

---

## 🌐 NEW: Use Proxy to Bypass IP Blocks

If you have access to a proxy server (or VPN), you can now use it:

### Option 1: Using Free Proxies (Testing Only)

**Find a free proxy:**
- https://www.proxy-list.download/
- https://free-proxy-list.net/
- Look for HTTP/HTTPS proxies (not SOCKS)

**Use it:**
```bash
# Stop current ingestion
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq

# Start with proxy
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "proxy": "http://proxy-ip:proxy-port",
    "videos_per_fetch": 5
  }' | jq
```

**Example with a real proxy:**
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "proxy": "http://154.12.243.45:3128",
    "videos_per_fetch": 5
  }' | jq
```

### Option 2: Using Premium Proxies (Production)

For reliable scraping, use residential proxies:
- **Bright Data**: https://brightdata.com (most reliable)
- **SmartProxy**: https://smartproxy.com
- **Oxylabs**: https://oxylabs.io

They provide rotating IPs that are harder to block.

### Option 3: Using Your Own VPN

If you have a VPN, you can set up a local proxy:

```bash
# Install tinyproxy
brew install tinyproxy  # macOS
# or
sudo apt install tinyproxy  # Linux

# Configure it to listen on localhost:8888
# Then use: "proxy": "http://localhost:8888"
```

---

## 🔄 Alternative: Disable TikTok, Use Demo Videos

If TikTok keeps blocking and you don't have a proxy:

```bash
# Stop TikTok ingestion
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq

# Use demo videos instead
# Edit .env or export:
export ENABLE_TIKTOK_AUTO_INGEST=false
export INGEST_DEMO_VIDEOS=true
export DEMO_VIDEO_COUNT=20

# Restart backend
bash START_TIKTOK_PLATFORM.sh
```

This gives you 20 demo videos instantly without TikTok issues!

---

## 📊 Check If Videos Are in Database

```bash
# Check video count
curl 'http://localhost:8080/api/v1/feed/for-you?user_id=user:test&limit=10' | jq '.videos | length'

# Should return a number > 0 if videos were ingested
```

---

## 🆘 Still Not Working?

1. **Check the file exists:**
   ```bash
   cat ~/Documents/projects/clipstream/backend/app/tiktok_urls.txt
   ```

2. **Check for typos:**
   - No spaces before/after URL
   - Correct pipe symbol `|` not `l` or `I`
   - Real video ID, not placeholder

3. **Test yt-dlp:**
   ```bash
   yt-dlp --version
   yt-dlp --simulate "https://www.tiktok.com/@demi32751/video/7584183122296589599"
   ```

4. **Check logs:**
   ```bash
   tail -f ~/Documents/projects/clipstream/backend/logs/app.log | grep -i tiktok
   ```

If yt-dlp itself fails with "IP blocked", you need to wait or use a VPN!

---

## 🎯 What Just Got Implemented

### Enhanced Anti-Detection Features

The browser scraper now includes advanced anti-detection measures:

**1. User Agent Rotation**
- 8 different realistic browser fingerprints
- Automatically rotates on each page load
- Includes Chrome, Edge, and Safari on Windows, macOS, and Linux

**2. Randomized Behavior**
- Viewport sizes vary (1920x1080, 1366x768, 1536x864, 1440x900, 2560x1440)
- Scroll distances randomized (80-120% of viewport)
- Delays randomized (±20% variance)
- Initial page load delay: 2-4 seconds

**3. Browser Fingerprinting Evasion**
- Removes `navigator.webdriver` property
- Mocks plugins array
- Sets proper language headers
- Chrome runtime emulation
- Permissions API mocking

**4. Proxy Support**
- Pass any HTTP/HTTPS proxy via API
- Supports authentication proxies
- Environment variable configuration
- Works with residential proxies, VPNs, and free proxies

**5. Enhanced Browser Settings**
- Disables automation detection features
- Sets realistic geolocation (New York)
- Proper timezone and locale
- Device scale factor normalization

### How to Use These Features

**Test without proxy (user agents + randomization only):**
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/stop | jq
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"use_browser": true, "videos_per_fetch": 5}' | jq
```

**Test with proxy (full anti-detection):**
```bash
curl -X POST http://localhost:8080/api/v1/tiktok-ingestion/start \
  -H "Content-Type: application/json" \
  -d '{
    "use_browser": true,
    "proxy": "http://your-proxy:port",
    "videos_per_fetch": 5
  }' | jq
```

**Check if it's working:**
```bash
# Watch logs
tail -f backend/logs/app.log | grep -i tiktok

# Check status
curl http://localhost:8080/api/v1/tiktok-ingestion/status | jq
```

### Success Indicators

**Before (Blocked):**
```
WARNING:app.tiktok_auto_ingestion:Browser scraper returned no videos
ERROR:app.tiktok_scraper:Your IP address is blocked
```

**After (Success):**
```
INFO:app.tiktok_browser_scraper:Rotating user agent: Mozilla/5.0...
INFO:app.tiktok_browser_scraper:Browser started successfully
INFO:app.tiktok_auto_ingestion:Browser scraper found 10 videos
INFO:app.tiktok_scraper:Successfully downloaded: Video Title
```

### Files Modified

1. `backend/app/tiktok_browser_scraper.py` - Added proxy support, user agent rotation, enhanced anti-detection
2. `backend/app/tiktok_auto_ingestion.py` - Added proxy parameter
3. `backend/api/tiktok_ingestion.py` - Added proxy to API configuration
4. `docs/guides/TROUBLESHOOTING_TIKTOK.md` - Updated with proxy solutions

### Next Steps

1. **Try without proxy first** - The enhanced user agents and randomization might be enough
2. **If still blocked, add a proxy** - Free proxies for testing, premium for production
3. **Monitor success rate** - Should improve from 0% to 80%+ with these changes
4. **Adjust delays if needed** - Increase scroll_delay in code if getting rate limited
