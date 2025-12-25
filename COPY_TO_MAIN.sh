#!/bin/bash

echo "📋 Copying Files from Worktree to Main Repository"
echo "=================================================="
echo ""

WORKTREE="/Users/issamnaim/.claude-worktrees/clipstream/cranky-johnson"
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

# Copy backend files
echo "📦 Copying backend files..."

cp "$WORKTREE/backend/app/startup.py" "$MAIN_REPO/backend/app/" && echo "  ✓ startup.py"
cp "$WORKTREE/backend/app/ingestion_engine.py" "$MAIN_REPO/backend/app/" && echo "  ✓ ingestion_engine.py"
cp "$WORKTREE/backend/app/scoring.py" "$MAIN_REPO/backend/app/" && echo "  ✓ scoring.py"
cp "$WORKTREE/backend/app/event_logger.py" "$MAIN_REPO/backend/app/" && echo "  ✓ event_logger.py"
cp "$WORKTREE/backend/app/initial_videos.py" "$MAIN_REPO/backend/app/" && echo "  ✓ initial_videos.py (with 13 real videos!)"
cp "$WORKTREE/backend/app/tiktok_scraper.py" "$MAIN_REPO/backend/app/" && echo "  ✓ tiktok_scraper.py"
cp "$WORKTREE/backend/app/embeddings.py" "$MAIN_REPO/backend/app/" && echo "  ✓ embeddings.py (NEW - Collision-less)"

cp "$WORKTREE/backend/api/events.py" "$MAIN_REPO/backend/api/" && echo "  ✓ events.py"
cp "$WORKTREE/backend/api/feed.py" "$MAIN_REPO/backend/api/" && echo "  ✓ feed.py"
cp "$WORKTREE/backend/api/infinite_feed.py" "$MAIN_REPO/backend/api/" && echo "  ✓ infinite_feed.py (NEW)"
cp "$WORKTREE/backend/api/realtime_events.py" "$MAIN_REPO/backend/api/" && echo "  ✓ realtime_events.py (NEW)"
cp "$WORKTREE/backend/api/embeddings_api.py" "$MAIN_REPO/backend/api/" && echo "  ✓ embeddings_api.py (NEW)"

cp "$WORKTREE/backend/main.py" "$MAIN_REPO/backend/" && echo "  ✓ main.py"

cp "$WORKTREE/backend/.env.example" "$MAIN_REPO/backend/" && echo "  ✓ .env.example"
cp "$WORKTREE/backend/.env.production" "$MAIN_REPO/backend/" && echo "  ✓ .env.production"
cp "$WORKTREE/backend/seed_real_videos.py" "$MAIN_REPO/backend/" && echo "  ✓ seed_real_videos.py"

# Copy backend documentation
echo ""
echo "📄 Copying backend documentation..."

cp "$WORKTREE/backend/STARTUP_LIFECYCLE.md" "$MAIN_REPO/backend/" && echo "  ✓ STARTUP_LIFECYCLE.md"
cp "$WORKTREE/backend/IMPLEMENTATION_SUMMARY.md" "$MAIN_REPO/backend/" && echo "  ✓ IMPLEMENTATION_SUMMARY.md"
cp "$WORKTREE/backend/TESTING_GUIDE.md" "$MAIN_REPO/backend/" && echo "  ✓ TESTING_GUIDE.md"

# Copy organized docs folder (RAG-ready)
echo ""
echo "📚 Copying organized docs folder..."

mkdir -p "$MAIN_REPO/docs"
cp -r "$WORKTREE/docs/"* "$MAIN_REPO/docs/" && echo "  ✓ docs/ (RAG knowledge base)"

# Copy root files
echo ""
echo "📄 Copying root files..."

cp "$WORKTREE/REAL_VIDEOS_READY.md" "$MAIN_REPO/" && echo "  ✓ REAL_VIDEOS_READY.md"
cp "$WORKTREE/READY_TO_PUSH.md" "$MAIN_REPO/" && echo "  ✓ READY_TO_PUSH.md"
cp "$WORKTREE/FINAL_SUMMARY.md" "$MAIN_REPO/" && echo "  ✓ FINAL_SUMMARY.md"
cp "$WORKTREE/TIKTOK_REALTIME_GUIDE.md" "$MAIN_REPO/" && echo "  ✓ TIKTOK_REALTIME_GUIDE.md (NEW)"
cp "$WORKTREE/TIKTOK_COMPLETE_SUMMARY.md" "$MAIN_REPO/" && echo "  ✓ TIKTOK_COMPLETE_SUMMARY.md (NEW)"
cp "$WORKTREE/EMBEDDINGS_GUIDE.md" "$MAIN_REPO/" && echo "  ✓ EMBEDDINGS_GUIDE.md (NEW)"
cp "$WORKTREE/FINAL_COMPLETE.md" "$MAIN_REPO/" && echo "  ✓ FINAL_COMPLETE.md (NEW)"
cp "$WORKTREE/DOCS_ORGANIZED.md" "$MAIN_REPO/" && echo "  ✓ DOCS_ORGANIZED.md (NEW)"
cp "$WORKTREE/frontend_tiktok_swipe.html" "$MAIN_REPO/" && echo "  ✓ frontend_tiktok_swipe.html (NEW)"
cp "$WORKTREE/TEST_NOW.sh" "$MAIN_REPO/" && echo "  ✓ TEST_NOW.sh"
cp "$WORKTREE/START_TIKTOK_PLATFORM.sh" "$MAIN_REPO/" && echo "  ✓ START_TIKTOK_PLATFORM.sh (NEW)"
cp "$WORKTREE/START_HERE_TIKTOK.md" "$MAIN_REPO/" && echo "  ✓ START_HERE_TIKTOK.md (NEW)"
chmod +x "$MAIN_REPO/TEST_NOW.sh"
chmod +x "$MAIN_REPO/START_TIKTOK_PLATFORM.sh"

echo ""
echo "✅ All files copied successfully!"
echo ""
echo "Next steps:"
echo "1. cd $MAIN_REPO"
echo "2. git status (check which files changed)"
echo "3. git add . (stage all changes)"
echo "4. git commit -m \"Add ML backend with real videos\""
echo "5. git push origin main"
echo ""
echo "Or run: bash PUSH_TO_MAIN.sh"
echo ""
