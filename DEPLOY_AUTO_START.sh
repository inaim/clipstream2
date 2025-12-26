#!/bin/bash

echo "🚀 Deploying TikTok Auto-Start Feature"
echo "======================================"
echo ""

cd ~/Documents/projects/clipstream || exit 1

echo "📦 Copying updated main.py..."
cp ~/.claude-worktrees/clipstream/cool-knuth/backend/main.py backend/main.py
echo "  ✓ main.py updated"

echo ""
echo "📊 Checking changes..."
git diff backend/main.py | head -50

echo ""
echo "📦 Staging changes..."
git add backend/main.py

echo ""
echo "📝 Creating commit..."
git commit -m "Enable TikTok auto-ingestion on app startup

- Changed default ENABLE_TIKTOK_AUTO_INGEST from false to true
- TikTok video scraping now starts automatically when app launches
- Enhanced startup logging for better visibility
- Scrapes trending hashtags every 5 minutes by default
- Browser scraping enabled with Playwright headless Chromium

Features:
- Auto-start on app launch (disable with ENABLE_TIKTOK_AUTO_INGEST=false)
- Default: 10 videos every 5 minutes
- Sources: #fyp, #viral, #trending, etc.
- Configurable via API after startup

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo ""
echo "🚀 Pushing to main..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully deployed!"
    echo ""
    echo "🎉 TikTok auto-ingestion will now start automatically when you launch the app!"
    echo ""
    echo "Next steps:"
    echo "1. Make sure Playwright is installed:"
    echo "   cd backend && playwright install chromium"
    echo ""
    echo "2. Restart your backend:"
    echo "   python backend/main.py"
    echo ""
    echo "3. Watch the logs for:"
    echo "   [STEP 3.5] Starting TikTok auto-ingestion with browser scraping..."
    echo "   ✅ TikTok auto-ingestion service started"
    echo ""
    echo "4. Videos will appear in your feeds every 5 minutes!"
else
    echo ""
    echo "❌ Push failed. Manual push needed:"
    echo "   cd ~/Documents/projects/clipstream"
    echo "   git push origin main"
fi
