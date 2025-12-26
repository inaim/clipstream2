#!/bin/bash

echo "🔄 Fixing Git Conflicts and Pushing TikTok Browser Scraping"
echo "==========================================================="
echo ""

cd ~/Documents/projects/clipstream || exit 1

echo "📥 Step 1: Pull latest changes from remote..."
git pull origin main --rebase

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Rebase conflict detected. Resolving..."
    echo ""

    # If there are conflicts, we need to resolve them
    echo "Checking for conflicts..."
    git status

    echo ""
    echo "If there are conflicts, you have two options:"
    echo ""
    echo "Option A: Accept all incoming changes (RECOMMENDED if remote is newer)"
    echo "  git checkout --theirs ."
    echo "  git add ."
    echo "  git rebase --continue"
    echo ""
    echo "Option B: Keep your local changes"
    echo "  git checkout --ours ."
    echo "  git add ."
    echo "  git rebase --continue"
    echo ""
    echo "After resolving, run this script again."
    exit 1
fi

echo "✅ Successfully pulled latest changes"
echo ""

echo "📦 Step 2: Copy new TikTok browser scraping files..."

# Copy files from worktree
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_browser_scraper.py backend/app/ && echo "  ✓ tiktok_browser_scraper.py"
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_auto_ingestion.py backend/app/ && echo "  ✓ tiktok_auto_ingestion.py"
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/api/tiktok_ingestion.py backend/api/ && echo "  ✓ tiktok_ingestion.py"
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/requirements.txt backend/ && echo "  ✓ requirements.txt"
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/TIKTOK_BROWSER_SCRAPING.md backend/ && echo "  ✓ TIKTOK_BROWSER_SCRAPING.md"

echo ""
echo "📊 Step 3: Check git status..."
git status --short

echo ""
echo "📦 Step 4: Stage all changes..."
git add backend/app/tiktok_browser_scraper.py
git add backend/app/tiktok_auto_ingestion.py
git add backend/api/tiktok_ingestion.py
git add backend/requirements.txt
git add backend/TIKTOK_BROWSER_SCRAPING.md

echo ""
echo "✅ Files staged"
echo ""

echo "📝 Step 5: Create commit..."

git commit -m "Add TikTok browser scraping with Playwright automation

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
  \"use_browser\": true,
  \"videos_per_fetch\": 20,
  \"fetch_interval\": 300
}

INSTALLATION:
pip install -r backend/requirements.txt
playwright install chromium

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo ""
echo "✅ Commit created"
echo ""

echo "🚀 Step 6: Push to main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to main!"
    echo ""
    echo "🎉 TikTok browser scraping is now live!"
    echo ""
    echo "Next steps:"
    echo "1. Install dependencies: pip install -r backend/requirements.txt"
    echo "2. Install Playwright browsers: playwright install chromium"
    echo "3. Start the backend and test the scraper"
    echo "4. Read documentation: backend/TIKTOK_BROWSER_SCRAPING.md"
else
    echo ""
    echo "❌ Push failed. Check the error above."
    echo ""
    echo "Common issues:"
    echo "- Remote has newer changes: Run 'git pull origin main --rebase' first"
    echo "- Authentication issues: Check your GitHub credentials"
    echo "- Branch protection: You may need to create a PR instead"
fi
