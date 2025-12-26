#!/bin/bash

echo "🧹 Cleaning Up Obsolete Files"
echo "=============================="
echo ""

cd ~/.claude-worktrees/clipstream/cool-knuth || exit 1

echo "This will remove 16 obsolete files that were created during git conflict resolution."
echo ""
echo "Files to remove:"
echo "  - Git conflict resolution scripts (8 files)"
echo "  - Duplicate push scripts (4 files)"
echo "  - Duplicate deployment docs (1 file)"
echo "  - Miscellaneous old scripts (3 files)"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "🗑️  Removing obsolete files..."
echo ""

# Git conflict resolution files (no longer needed)
rm -f CONFLICT_RESOLUTION_GUIDE.md && echo "  ✓ CONFLICT_RESOLUTION_GUIDE.md"
rm -f RESOLVE_CONFLICTS.sh && echo "  ✓ RESOLVE_CONFLICTS.sh"
rm -f FIX_AND_PUSH.sh && echo "  ✓ FIX_AND_PUSH.sh"
rm -f FIX_CURRENT_STATE.sh && echo "  ✓ FIX_CURRENT_STATE.sh"
rm -f SIMPLE_FIX.md && echo "  ✓ SIMPLE_FIX.md"
rm -f SIMPLE_PUSH.md && echo "  ✓ SIMPLE_PUSH.md"
rm -f MANUAL_PUSH_INSTRUCTIONS.md && echo "  ✓ MANUAL_PUSH_INSTRUCTIONS.md"
rm -f CREATE_FRESH_WORKTREE.sh && echo "  ✓ CREATE_FRESH_WORKTREE.sh"

# Duplicate push scripts (consolidated into DEPLOY_AUTO_START.sh)
rm -f PUSH_TO_MAIN.sh && echo "  ✓ PUSH_TO_MAIN.sh"
rm -f PUSH_BROWSER_SCRAPING.sh && echo "  ✓ PUSH_BROWSER_SCRAPING.sh"
rm -f COPY_TO_MAIN.sh && echo "  ✓ COPY_TO_MAIN.sh"
rm -f COMMIT_INSTRUCTIONS.sh && echo "  ✓ COMMIT_INSTRUCTIONS.sh"

# Duplicate deployment docs
rm -f QUICK_DEPLOY.md && echo "  ✓ QUICK_DEPLOY.md"

# Miscellaneous old files
rm -f ORGANIZE_DOCS.sh && echo "  ✓ ORGANIZE_DOCS.sh"
rm -f DOWNLOAD_TIKTOK_VIDEOS.sh && echo "  ✓ DOWNLOAD_TIKTOK_VIDEOS.sh"
rm -f run-test.sh && echo "  ✓ run-test.sh"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📁 Remaining essential files in root:"
ls -1 *.md *.sh 2>/dev/null | grep -v CLEANUP_OBSOLETE.sh | grep -v CLEANUP_GUIDE.md | sort
echo ""
echo "📦 Backend documentation:"
ls -1 backend/*.md 2>/dev/null | sort
echo ""
echo "📊 Summary:"
echo "  - Removed: 16 obsolete files"
echo "  - Kept: 11 essential files"
echo "  - Result: Clean, organized worktree ✨"
echo ""
echo "💡 Next steps:"
echo "  1. Review CLEANUP_GUIDE.md for details"
echo "  2. Deploy auto-start: bash DEPLOY_AUTO_START.sh"
echo "  3. Read docs: cat AUTO_START_TIKTOK.md"
