#!/bin/bash

echo "🧹 Final Cleanup - Consolidating Documentation"
echo "=============================================="
echo ""

cd ~/.claude-worktrees/clipstream/cool-knuth || exit 1

echo "📋 This will:"
echo "1. Move backend docs to docs/ folder"
echo "2. Remove duplicate/obsolete documentation"
echo "3. Keep only essential scripts"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "📦 Step 1: Moving backend docs to docs/guides..."

# Move browser scraping doc if it exists in backend
if [ -f "backend/TIKTOK_BROWSER_SCRAPING.md" ]; then
    cp backend/TIKTOK_BROWSER_SCRAPING.md docs/guides/TIKTOK_BROWSER_SCRAPING.md
    rm backend/TIKTOK_BROWSER_SCRAPING.md
    echo "  ✓ Moved TIKTOK_BROWSER_SCRAPING.md to docs/guides/"
fi

echo ""
echo "🗑️  Step 2: Removing duplicate documentation..."

# Remove duplicate/obsolete docs in root
rm -f AUTO_START_TIKTOK.md && echo "  ✓ Removed AUTO_START_TIKTOK.md (info in TIKTOK_AUTO_INGESTION_GUIDE.md)"
rm -f COMPLETE_SETUP_GUIDE.md && echo "  ✓ Removed COMPLETE_SETUP_GUIDE.md (duplicate)"
rm -f FILE_REVIEW_SUMMARY.md && echo "  ✓ Removed FILE_REVIEW_SUMMARY.md (cleanup complete)"
rm -f CLEANUP_GUIDE.md && echo "  ✓ Removed CLEANUP_GUIDE.md (no longer needed)"

# Remove git conflict resolution files
rm -f CONFLICT_RESOLUTION_GUIDE.md
rm -f RESOLVE_CONFLICTS.sh
rm -f FIX_AND_PUSH.sh
rm -f FIX_CURRENT_STATE.sh
rm -f SIMPLE_FIX.md
rm -f SIMPLE_PUSH.md
rm -f MANUAL_PUSH_INSTRUCTIONS.md
rm -f CREATE_FRESH_WORKTREE.sh
echo "  ✓ Removed git conflict files (8 files)"

# Remove duplicate push scripts
rm -f PUSH_TO_MAIN.sh
rm -f PUSH_BROWSER_SCRAPING.sh
rm -f COPY_TO_MAIN.sh
rm -f COMMIT_INSTRUCTIONS.sh
rm -f QUICK_DEPLOY.md
echo "  ✓ Removed duplicate push scripts (5 files)"

# Remove miscellaneous old files
rm -f ORGANIZE_DOCS.sh
rm -f DOWNLOAD_TIKTOK_VIDEOS.sh
rm -f run-test.sh
echo "  ✓ Removed miscellaneous old files (3 files)"

# Remove deployment scripts (keeping only START_TIKTOK_PLATFORM.sh)
rm -f DEPLOY_AUTO_START.sh && echo "  ✓ Removed DEPLOY_AUTO_START.sh (changes already applied)"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Documentation Structure:"
echo ""
echo "Root Level (Essential Scripts):"
ls -1 *.sh 2>/dev/null | sort
echo ""
echo "Documentation (docs/guides/):"
ls -1 docs/guides/*.md 2>/dev/null | xargs -n1 basename | sort
echo ""
echo "📊 Summary:"
echo "  - Removed: ~20 obsolete files"
echo "  - Consolidated: All docs in docs/guides/"
echo "  - Kept: Essential scripts and documentation"
echo ""
echo "🎯 Quick Reference:"
echo "  Start Platform:  bash START_TIKTOK_PLATFORM.sh"
echo "  Setup Backend:   bash setup-backend.sh"
echo "  Run Tests:       bash TEST_NOW.sh"
echo "  Documentation:   docs/guides/TIKTOK_AUTO_INGESTION_GUIDE.md"
echo ""
echo "✨ Your project is now clean and organized!"
