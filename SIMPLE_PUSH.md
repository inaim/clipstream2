# Simple Push Instructions

The push failed because the remote branch has newer commits. Here's how to fix it:

## Option 1: Quick Fix (Recommended)

Run this single command in your terminal:

```bash
bash ~/.claude-worktrees/clipstream/cool-knuth/FIX_AND_PUSH.sh
```

This will:
1. Pull latest changes from remote
2. Copy your new files
3. Stage and commit them
4. Push to main

---

## Option 2: Manual Step-by-Step

If the script doesn't work, run these commands manually:

### Step 1: Navigate to main repository
```bash
cd ~/Documents/projects/clipstream
```

### Step 2: Pull latest changes
```bash
git pull origin main --rebase
```

If you get conflicts, resolve them:
```bash
# See what's conflicting
git status

# Accept remote changes (if remote is newer)
git checkout --theirs .
git add .
git rebase --continue

# OR accept your changes
git checkout --ours .
git add .
git rebase --continue
```

### Step 3: Copy new files
```bash
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_browser_scraper.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/app/tiktok_auto_ingestion.py backend/app/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/api/tiktok_ingestion.py backend/api/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/requirements.txt backend/
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/TIKTOK_BROWSER_SCRAPING.md backend/
```

### Step 4: Stage and commit
```bash
git add backend/app/tiktok_browser_scraper.py \
        backend/app/tiktok_auto_ingestion.py \
        backend/api/tiktok_ingestion.py \
        backend/requirements.txt \
        backend/TIKTOK_BROWSER_SCRAPING.md

git commit -m "Add TikTok browser scraping with Playwright

- Headless browser automation
- Infinite scroll support
- Multi-source scraping (trending, hashtags, profiles)
- Real-time metadata extraction

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Step 5: Push
```bash
git push origin main
```

---

## Option 3: Force Push (Use with Caution)

⚠️ **Only use this if you're sure you want to overwrite remote changes:**

```bash
cd ~/Documents/projects/clipstream
git push origin main --force
```

**Warning:** This will discard any changes on the remote that aren't in your local branch!

---

## Option 4: Create a Pull Request

If the main branch is protected, create a new branch and PR:

```bash
cd ~/Documents/projects/clipstream

# Create new branch
git checkout -b feature/tiktok-browser-scraping

# Copy files
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

git commit -m "Add TikTok browser scraping with Playwright automation"

# Push to new branch
git push origin feature/tiktok-browser-scraping

# Create PR on GitHub
# Go to: https://github.com/inaim/clipstream2/pulls
# Click "New Pull Request"
# Select feature/tiktok-browser-scraping -> main
```

---

## Troubleshooting

### Error: "non-fast-forward"
**Cause:** Remote has commits you don't have locally
**Solution:** Pull with rebase first (Option 2, Step 2)

### Error: "Operation not permitted"
**Cause:** Permission issues with directory
**Solution:**
1. Check directory permissions: `ls -la ~/Documents/projects/clipstream`
2. Try running with sudo: `sudo bash FIX_AND_PUSH.sh` (not recommended)
3. Clone the repo fresh in a different location

### Error: "merge conflict"
**Cause:** Same files edited in both local and remote
**Solution:** Follow Step 2 conflict resolution above

### Error: "Authentication failed"
**Cause:** GitHub credentials issue
**Solution:**
1. Set up SSH: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Add to GitHub: Settings > SSH Keys
3. Or use personal access token

---

## What's Being Pushed

**Files (5 total):**
1. ✨ `backend/app/tiktok_browser_scraper.py` (NEW)
2. ✨ `backend/TIKTOK_BROWSER_SCRAPING.md` (NEW)
3. 🔄 `backend/app/tiktok_auto_ingestion.py` (UPDATED)
4. 🔄 `backend/api/tiktok_ingestion.py` (UPDATED)
5. 🔄 `backend/requirements.txt` (UPDATED)

**Changes:**
- ~500 lines: New browser scraper
- ~300 lines: Documentation
- ~100 lines: Integration updates
- Total: ~900 lines of production code

---

## After Successful Push

Install and test:

```bash
# Install dependencies
pip install -r backend/requirements.txt
playwright install chromium

# Test the scraper
cd backend
python -m app.tiktok_browser_scraper

# Start auto-ingestion
curl -X POST http://localhost:8000/api/tiktok_ingestion/start \
  -H "Content-Type: application/json" \
  -d '{"use_browser": true, "videos_per_fetch": 20}'
```

Read the docs:
```bash
cat backend/TIKTOK_BROWSER_SCRAPING.md
```
