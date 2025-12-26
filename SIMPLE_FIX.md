# Simple Fix - Push Browser Scraping to Main

## Your Current Situation

You're on `docs/cleanup` branch with uncommitted changes, trying to push to `main`.

## Quick Fix (Copy & Paste)

Run these commands in your terminal:

```bash
cd ~/Documents/projects/clipstream

# Save your current work
git stash

# Switch to main and update
git checkout main
git pull origin main

# Copy browser scraping files
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_browser_scraper.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_auto_ingestion.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/api/tiktok_ingestion.py backend/api/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/requirements.txt backend/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/TIKTOK_BROWSER_SCRAPING.md backend/

# Commit and push
git add backend/app/tiktok_browser_scraper.py backend/app/tiktok_auto_ingestion.py backend/api/tiktok_ingestion.py backend/requirements.txt backend/TIKTOK_BROWSER_SCRAPING.md
git commit -m "Add TikTok browser scraping with Playwright automation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push origin main
```

Done! ✅

## If You Want Your Stashed Changes Back

After pushing, restore your docs/cleanup work:

```bash
git checkout docs/cleanup
git stash pop
```

## Alternative: Automated Script

Run this:

```bash
bash ~/.claude-worktrees/clipstream/cool-knuth/FIX_CURRENT_STATE.sh
```

## Why This Happened

Your worktree (`cool-knuth`) was created from an old commit, not from the latest `origin/main`. This caused conflicts.

### Better Workflow for Next Time

When creating a worktree, always use latest origin:

```bash
cd ~/Documents/projects/clipstream
git fetch origin
git worktree add -b new-feature ~/.claude-worktrees/clipstream/new-feature origin/main
```

This creates a worktree from the latest `origin/main`, avoiding conflicts.

## Summary

1. ✅ Stash your current changes on docs/cleanup
2. ✅ Switch to main branch
3. ✅ Pull latest from origin
4. ✅ Copy browser scraping files
5. ✅ Commit and push
6. ✅ (Optional) Go back to docs/cleanup and restore stashed changes
