# Git Conflict Resolution Guide

You have conflicts in the `cool-knuth` branch that need to be resolved before pushing to main.

## Conflicting Files

1. `COPY_TO_MAIN.sh` - Helper script
2. `DOWNLOAD_TIKTOK_VIDEOS.sh` - Helper script
3. `backend/api/tiktok_ingestion.py` - **IMPORTANT** (has browser scraping)
4. `backend/app/tiktok_auto_ingestion.py` - **IMPORTANT** (has browser scraping)
5. `backend/main.py` - Backend entry point
6. `tiktok_urls.txt` - Test URLs

## Quick Resolution (Recommended)

### Option 1: Keep Our Browser Scraping Changes

Run this from your main repository:

```bash
cd ~/Documents/projects/clipstream

# Keep our changes for critical backend files (browser scraping implementation)
git checkout cool-knuth
git checkout --ours backend/api/tiktok_ingestion.py
git checkout --ours backend/app/tiktok_auto_ingestion.py

# Keep main branch version for helper scripts
git checkout --theirs COPY_TO_MAIN.sh
git checkout --theirs DOWNLOAD_TIKTOK_VIDEOS.sh
git checkout --theirs tiktok_urls.txt
git checkout --theirs backend/main.py

# Stage resolved files
git add backend/api/tiktok_ingestion.py
git add backend/app/tiktok_auto_ingestion.py
git add COPY_TO_MAIN.sh
git add DOWNLOAD_TIKTOK_VIDEOS.sh
git add tiktok_urls.txt
git add backend/main.py

# Continue the merge/rebase
git rebase --continue
# OR if you were merging:
# git merge --continue

# Then push
git push origin cool-knuth
```

### Option 2: Use Automated Script

```bash
cd ~/.claude-worktrees/clipstream/cool-knuth
bash RESOLVE_CONFLICTS.sh
```

## Manual Resolution

If you prefer to resolve conflicts manually:

### Step 1: Navigate to repository

```bash
cd ~/Documents/projects/clipstream
git checkout cool-knuth
```

### Step 2: Check conflict status

```bash
git status
```

You should see files marked as "both modified".

### Step 3: Resolve each file

For each file, you have three options:

**A) Keep our version (--ours):**
```bash
git checkout --ours <file>
```

**B) Keep their version (--theirs):**
```bash
git checkout --theirs <file>
```

**C) Manually edit the file:**
```bash
# Open in your editor
code <file>  # or vim, nano, etc.

# Look for conflict markers:
<<<<<<< HEAD (current change)
our changes
=======
their changes
>>>>>>> branch-name (incoming change)

# Edit to keep what you want, remove conflict markers
# Save the file
```

### Step 4: Recommended Resolution Strategy

```bash
cd ~/Documents/projects/clipstream
git checkout cool-knuth

# KEEP OURS (browser scraping implementation) for these:
git checkout --ours backend/api/tiktok_ingestion.py
git checkout --ours backend/app/tiktok_auto_ingestion.py

# KEEP THEIRS (main branch) for these:
git checkout --theirs COPY_TO_MAIN.sh
git checkout --theirs DOWNLOAD_TIKTOK_VIDEOS.sh
git checkout --theirs tiktok_urls.txt
git checkout --theirs backend/main.py

# Stage all resolved files
git add .
```

### Step 5: Complete the merge/rebase

```bash
# If you were rebasing:
git rebase --continue

# If you were merging:
git merge --continue

# If neither, create a commit:
git commit -m "Resolve conflicts - keep browser scraping implementation"
```

### Step 6: Push to remote

```bash
git push origin cool-knuth
```

## Understanding the Conflicts

### Critical Files (Keep OURS):

**backend/api/tiktok_ingestion.py**
- Contains new `use_browser` parameter
- Updated `IngestionConfig` and `IngestionStatus` models
- Essential for browser scraping configuration

**backend/app/tiktok_auto_ingestion.py**
- Contains browser scraper integration
- New `_get_trending_tiktok_urls()` implementation
- Browser lifecycle management (start/stop)
- Metadata merging logic

**Why keep OURS?** These files contain the complete TikTok browser scraping implementation we just built.

### Non-Critical Files (Keep THEIRS):

**COPY_TO_MAIN.sh, DOWNLOAD_TIKTOK_VIDEOS.sh**
- Helper scripts that may have been updated in main
- Don't affect core functionality

**tiktok_urls.txt**
- Test data file
- Can use latest from main

**backend/main.py**
- May have other updates in main branch
- Our changes don't modify this file

## After Resolution

### 1. Verify the changes

```bash
git status
git diff --cached
```

### 2. Test the resolved code

```bash
cd backend
python -m app.tiktok_browser_scraper
```

### 3. Push to main

Once conflicts are resolved and committed:

```bash
# If on cool-knuth branch, merge to main:
git checkout main
git merge cool-knuth
git push origin main

# OR push cool-knuth and create PR:
git checkout cool-knuth
git push origin cool-knuth
# Then create PR on GitHub
```

## Troubleshooting

### "error: you need to resolve your current index first"

You have unresolved conflicts. Run:
```bash
git status
```
Look for files marked "both modified" and resolve them.

### "error: could not apply..."

The rebase failed. Options:
```bash
# Abort and start over:
git rebase --abort

# Or continue after resolving:
git rebase --continue
```

### "Already up to date"

You've already resolved the conflicts. Just push:
```bash
git push origin cool-knuth
```

## Alternative: Start Fresh

If conflicts are too complex, copy files to main directly:

```bash
cd ~/Documents/projects/clipstream
git checkout main
git pull origin main

# Copy our new files directly
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_browser_scraper.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_auto_ingestion.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/api/tiktok_ingestion.py backend/api/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/requirements.txt backend/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/TIKTOK_BROWSER_SCRAPING.md backend/

# Stage and commit
git add backend/app/tiktok_browser_scraper.py \
        backend/app/tiktok_auto_ingestion.py \
        backend/api/tiktok_ingestion.py \
        backend/requirements.txt \
        backend/TIKTOK_BROWSER_SCRAPING.md

git commit -m "Add TikTok browser scraping with Playwright automation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin main
```

This bypasses the worktree conflicts entirely.
