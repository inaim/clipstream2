#!/bin/bash

echo "🔧 Resolving Git Conflicts in cool-knuth Branch"
echo "==============================================="
echo ""

# Files with conflicts
CONFLICT_FILES=(
    "COPY_TO_MAIN.sh"
    "DOWNLOAD_TIKTOK_VIDEOS.sh"
    "backend/api/tiktok_ingestion.py"
    "backend/app/tiktok_auto_ingestion.py"
    "backend/main.py"
    "tiktok_urls.txt"
)

echo "Files with conflicts:"
for file in "${CONFLICT_FILES[@]}"; do
    echo "  - $file"
done
echo ""

echo "Resolution Strategy:"
echo "  - For backend files: Keep OUR changes (browser scraping implementation)"
echo "  - For script files: Keep THEIRS (from main branch)"
echo ""

read -p "Proceed with automatic conflict resolution? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "🔧 Resolving conflicts..."
echo ""

# For critical backend files with our new implementation, keep ours
echo "Keeping OUR version (with browser scraping):"
git checkout --ours backend/api/tiktok_ingestion.py && echo "  ✓ backend/api/tiktok_ingestion.py"
git checkout --ours backend/app/tiktok_auto_ingestion.py && echo "  ✓ backend/app/tiktok_auto_ingestion.py"

# For helper scripts and config, keep theirs from main
echo ""
echo "Keeping THEIRS version (from main):"
git checkout --theirs COPY_TO_MAIN.sh && echo "  ✓ COPY_TO_MAIN.sh"
git checkout --theirs DOWNLOAD_TIKTOK_VIDEOS.sh && echo "  ✓ DOWNLOAD_TIKTOK_VIDEOS.sh"
git checkout --theirs tiktok_urls.txt && echo "  ✓ tiktok_urls.txt"

# For backend/main.py, we need to check what the conflict is
echo ""
echo "Checking backend/main.py conflict..."
if git diff --name-only --diff-filter=U | grep -q "backend/main.py"; then
    echo "  backend/main.py has conflicts. Keeping THEIRS (from main) as baseline."
    git checkout --theirs backend/main.py
    echo "  ✓ backend/main.py (using main branch version)"
else
    echo "  ℹ backend/main.py - no active conflict"
fi

echo ""
echo "📦 Staging resolved files..."
for file in "${CONFLICT_FILES[@]}"; do
    if [ -f "$file" ]; then
        git add "$file" && echo "  ✓ Staged: $file"
    fi
done

echo ""
echo "✅ Conflicts resolved!"
echo ""
echo "Next steps:"
echo "1. Review the changes: git status"
echo "2. Continue the merge/rebase: git rebase --continue (or git merge --continue)"
echo "3. Or create a new commit: git commit -m \"Resolve conflicts - keep browser scraping changes\""
echo ""
