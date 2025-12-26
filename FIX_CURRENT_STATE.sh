#!/bin/bash

echo "🔧 Fixing Current Git State and Pushing Browser Scraping"
echo "========================================================="
echo ""

cd ~/Documents/projects/clipstream || exit 1

echo "Current situation:"
echo "  - On branch: docs/cleanup (not main!)"
echo "  - Modified: tiktok_urls.txt, docs/guides/TIKTOK_AUTO_INGESTION_GUIDE.md"
echo "  - Untracked: backend/app/tiktok_collector.py"
echo "  - Main branch is behind origin/main"
echo ""

echo "Solution:"
echo "  1. Stash or commit current changes on docs/cleanup"
echo "  2. Switch to main branch"
echo "  3. Pull latest from origin/main"
echo "  4. Copy browser scraping files"
echo "  5. Commit and push"
echo ""

read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "📦 Step 1: Stash current changes on docs/cleanup..."
git stash push -m "WIP: docs cleanup and tiktok_urls changes"
echo "  ✓ Changes stashed"

echo ""
echo "🌿 Step 2: Switch to main branch..."
git checkout main
echo "  ✓ Switched to main"

echo ""
echo "📥 Step 3: Pull latest from origin/main..."
git fetch origin
git pull origin main --rebase
echo "  ✓ Updated to latest main"

echo ""
echo "📦 Step 4: Copy browser scraping files..."

WORKTREE="$HOME/.claude-worktrees/clipstream/cool-knuth"

cp "$WORKTREE/backend/app/tiktok_browser_scraper.py" backend/app/ && echo "  ✓ tiktok_browser_scraper.py"
cp "$WORKTREE/backend/app/tiktok_auto_ingestion.py" backend/app/ && echo "  ✓ tiktok_auto_ingestion.py"
cp "$WORKTREE/backend/api/tiktok_ingestion.py" backend/api/ && echo "  ✓ tiktok_ingestion.py"
cp "$WORKTREE/backend/requirements.txt" backend/ && echo "  ✓ requirements.txt"
cp "$WORKTREE/backend/TIKTOK_BROWSER_SCRAPING.md" backend/ && echo "  ✓ TIKTOK_BROWSER_SCRAPING.md"

echo ""
echo "📊 Step 5: Check what changed..."
git status --short

echo ""
echo "📦 Step 6: Stage browser scraping files..."
git add backend/app/tiktok_browser_scraper.py
git add backend/app/tiktok_auto_ingestion.py
git add backend/api/tiktok_ingestion.py
git add backend/requirements.txt
git add backend/TIKTOK_BROWSER_SCRAPING.md

echo "  ✓ Files staged"

echo ""
echo "📝 Step 7: Create commit..."
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

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo ""
echo "✅ Commit created!"

echo ""
echo "🚀 Step 8: Push to origin/main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to origin/main!"
    echo ""
    echo "🎉 TikTok browser scraping is now live!"
    echo ""
    echo "📋 Next: Handle your stashed changes"
    echo "  Option A: Apply stash to docs/cleanup branch"
    echo "    git checkout docs/cleanup"
    echo "    git stash pop"
    echo "    git add ."
    echo "    git commit -m \"Update docs and tiktok URLs\""
    echo "    git push origin docs/cleanup"
    echo ""
    echo "  Option B: Discard stashed changes"
    echo "    git stash drop"
else
    echo ""
    echo "❌ Push failed."
    echo ""
    echo "Possible issues:"
    echo "1. Still behind origin/main - try: git pull origin main --rebase"
    echo "2. Authentication issue - check GitHub credentials"
    echo "3. Branch protection - create a PR instead"
    echo ""
    echo "To see stashed changes:"
    echo "  git stash list"
    echo "  git stash show"
fi

echo ""
echo "📍 Current branch: $(git branch --show-current)"
echo "📍 Status:"
git status --short
