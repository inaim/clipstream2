#!/bin/bash

echo "🚀 Pushing TikTok Browser Scraping to Main Repository"
echo "====================================================="
echo ""

WORKTREE="/Users/issamnaim/.claude-worktrees/clipstream/cool-knuth"
MAIN_REPO="/Users/issamnaim/Documents/projects/clipstream"

echo "Source: $WORKTREE"
echo "Target: $MAIN_REPO"
echo ""

# Check if directories exist
if [ ! -d "$WORKTREE" ]; then
    echo "❌ Worktree not found: $WORKTREE"
    exit 1
fi

if [ ! -d "$MAIN_REPO" ]; then
    echo "❌ Main repo not found: $MAIN_REPO"
    exit 1
fi

# Copy new browser scraping files
echo "📦 Copying browser scraping files..."

cp "$WORKTREE/backend/app/tiktok_browser_scraper.py" "$MAIN_REPO/backend/app/" && echo "  ✓ tiktok_browser_scraper.py (NEW)"
cp "$WORKTREE/backend/app/tiktok_auto_ingestion.py" "$MAIN_REPO/backend/app/" && echo "  ✓ tiktok_auto_ingestion.py (UPDATED)"
cp "$WORKTREE/backend/api/tiktok_ingestion.py" "$MAIN_REPO/backend/api/" && echo "  ✓ tiktok_ingestion.py (UPDATED)"
cp "$WORKTREE/backend/requirements.txt" "$MAIN_REPO/backend/" && echo "  ✓ requirements.txt (UPDATED - added playwright & yt-dlp)"

# Copy documentation
echo ""
echo "📄 Copying documentation..."
cp "$WORKTREE/backend/TIKTOK_BROWSER_SCRAPING.md" "$MAIN_REPO/backend/" && echo "  ✓ TIKTOK_BROWSER_SCRAPING.md (NEW)"

echo ""
echo "✅ All files copied successfully!"
echo ""

# Navigate to main repo and commit
echo "📝 Navigating to main repository..."
cd "$MAIN_REPO" || exit 1

echo ""
echo "📊 Git status:"
git status --short

echo ""
echo "📦 Staging changes..."
git add backend/app/tiktok_browser_scraper.py
git add backend/app/tiktok_auto_ingestion.py
git add backend/api/tiktok_ingestion.py
git add backend/requirements.txt
git add backend/TIKTOK_BROWSER_SCRAPING.md

echo ""
echo "✅ Files staged"
echo ""

echo "📝 Creating commit..."

git commit -m "$(cat <<'EOF'
Add TikTok browser scraping with headless automation

REAL-TIME TIKTOK FEED SCRAPING:
- Headless browser automation using Playwright
- Infinite scroll support for continuous feed scraping
- Multi-source scraping (trending, hashtags, user profiles)
- Real-time metadata extraction from DOM
- Anti-detection measures (user agent, automation flags)

NEW FILES:
- backend/app/tiktok_browser_scraper.py - Playwright-based scraper
- backend/TIKTOK_BROWSER_SCRAPING.md - Complete documentation

UPDATED FILES:
- backend/app/tiktok_auto_ingestion.py - Browser scraping integration
- backend/api/tiktok_ingestion.py - API configuration options
- backend/requirements.txt - Added playwright & yt-dlp

FEATURES:
- Scrape trending feed (/foryou)
- Scrape hashtag feeds (#fyp, #viral, etc.)
- Scrape user profiles (@username)
- Concurrent multi-hashtag scraping
- Automatic metadata extraction (views, likes, hashtags, creators)
- Fallback to manual URL lists
- Configurable via API (use_browser parameter)

HOW IT WORKS:
1. Browser launches headless Chromium
2. Navigates to TikTok feed
3. Infinite scroll to load more videos
4. Extracts video URLs and metadata from DOM
5. Downloads videos using yt-dlp
6. Ingests into database with real-time events

USAGE:
POST /api/tiktok_ingestion/start
{
  "use_browser": true,
  "videos_per_fetch": 20,
  "fetch_interval": 300
}

INSTALLATION:
pip install -r backend/requirements.txt
playwright install chromium

CONFIGURATION:
- Customizable hashtags for scraping
- Adjustable scroll delay and video limits
- Browser headless/visible mode toggle
- User agent customization

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

echo ""
echo "✅ Commit created"
echo ""

echo "🚀 Pushing to main..."
git push origin main

echo ""
echo "✅ Successfully pushed to main!"
echo ""
echo "🎉 TikTok browser scraping is now live!"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip install -r backend/requirements.txt"
echo "2. Install Playwright: playwright install chromium"
echo "3. Start auto-ingestion: POST /api/tiktok_ingestion/start"
echo "4. Read docs: backend/TIKTOK_BROWSER_SCRAPING.md"
echo ""
