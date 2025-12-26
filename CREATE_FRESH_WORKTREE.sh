#!/bin/bash

echo "🔄 Creating Fresh Worktree from Latest Origin"
echo "============================================="
echo ""

MAIN_REPO="$HOME/Documents/projects/clipstream"
WORKTREE_DIR="$HOME/.claude-worktrees/clipstream"
NEW_WORKTREE_NAME="tiktok-browser-scraping"
OLD_WORKTREE="$HOME/.claude-worktrees/clipstream/cool-knuth"

echo "This will:"
echo "1. Navigate to main repository"
echo "2. Fetch latest changes from origin"
echo "3. Create a NEW worktree from latest origin/main"
echo "4. Copy our browser scraping files to the new worktree"
echo "5. Clean up the old conflicted worktree"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "📍 Step 1: Navigate to main repository..."
cd "$MAIN_REPO" || exit 1
echo "  ✓ In: $(pwd)"

echo ""
echo "📥 Step 2: Fetch latest changes from origin..."
git fetch origin
echo "  ✓ Fetched latest changes"

echo ""
echo "🌿 Step 3: Create new worktree from origin/main..."
mkdir -p "$WORKTREE_DIR"

# Remove old worktree if it exists
if [ -d "$WORKTREE_DIR/$NEW_WORKTREE_NAME" ]; then
    echo "  ℹ  Removing existing worktree: $NEW_WORKTREE_NAME"
    git worktree remove "$WORKTREE_DIR/$NEW_WORKTREE_NAME" --force
fi

# Create new worktree from latest origin/main
git worktree add -b "$NEW_WORKTREE_NAME" "$WORKTREE_DIR/$NEW_WORKTREE_NAME" origin/main
echo "  ✓ Created worktree: $WORKTREE_DIR/$NEW_WORKTREE_NAME"

echo ""
echo "📦 Step 4: Copy browser scraping files to new worktree..."

# Copy our new files
cp "$OLD_WORKTREE/backend/app/tiktok_browser_scraper.py" "$WORKTREE_DIR/$NEW_WORKTREE_NAME/backend/app/" && echo "  ✓ tiktok_browser_scraper.py"
cp "$OLD_WORKTREE/backend/app/tiktok_auto_ingestion.py" "$WORKTREE_DIR/$NEW_WORKTREE_NAME/backend/app/" && echo "  ✓ tiktok_auto_ingestion.py"
cp "$OLD_WORKTREE/backend/api/tiktok_ingestion.py" "$WORKTREE_DIR/$NEW_WORKTREE_NAME/backend/api/" && echo "  ✓ tiktok_ingestion.py"
cp "$OLD_WORKTREE/backend/requirements.txt" "$WORKTREE_DIR/$NEW_WORKTREE_NAME/backend/" && echo "  ✓ requirements.txt"
cp "$OLD_WORKTREE/backend/TIKTOK_BROWSER_SCRAPING.md" "$WORKTREE_DIR/$NEW_WORKTREE_NAME/backend/" && echo "  ✓ TIKTOK_BROWSER_SCRAPING.md"

echo ""
echo "📊 Step 5: Check status in new worktree..."
cd "$WORKTREE_DIR/$NEW_WORKTREE_NAME"
git status --short

echo ""
echo "📦 Step 6: Stage changes in new worktree..."
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
echo "🚀 Step 8: Push to origin..."
git push origin "$NEW_WORKTREE_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to origin/$NEW_WORKTREE_NAME!"
    echo ""
    echo "🎉 Next steps:"
    echo "1. Create a Pull Request: https://github.com/inaim/clipstream2/compare/$NEW_WORKTREE_NAME"
    echo "2. Or merge directly to main:"
    echo "   cd $MAIN_REPO"
    echo "   git checkout main"
    echo "   git merge $NEW_WORKTREE_NAME"
    echo "   git push origin main"
    echo ""
    echo "🧹 Optional: Clean up old worktree"
    echo "   cd $MAIN_REPO"
    echo "   git worktree remove $OLD_WORKTREE --force"
else
    echo ""
    echo "❌ Push failed. But commit is ready locally."
    echo "You can push manually or create PR from GitHub."
fi

echo ""
echo "📍 New worktree location: $WORKTREE_DIR/$NEW_WORKTREE_NAME"
echo "📍 Old worktree location: $OLD_WORKTREE"
