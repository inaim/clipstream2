#!/bin/bash

echo "🎬 TikTok Video Downloader"
echo "=========================="
echo ""
echo "This script downloads REAL TikTok videos and adds them to your platform."
echo ""

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp not installed!"
    echo ""
    echo "Install it with:"
    echo "  pip install yt-dlp"
    echo "  # OR"
    echo "  brew install yt-dlp"
    echo ""
    exit 1
fi

echo "✅ yt-dlp found"
echo ""

# Create download directory
DOWNLOAD_DIR="./tiktok_videos"
mkdir -p "$DOWNLOAD_DIR"

echo "📁 Download directory: $DOWNLOAD_DIR"
echo ""

# Function to download and ingest a TikTok video
download_tiktok_video() {
    local url=$1
    local category=$2

    echo "📥 Downloading: $url"
    echo "   Category: $category"

    # Download video with yt-dlp
    yt-dlp \
        --format "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
        --output "$DOWNLOAD_DIR/%(id)s.%(ext)s" \
        --write-info-json \
        --quiet \
        "$url"

    if [ $? -eq 0 ]; then
        echo "   ✅ Downloaded successfully"
    else
        echo "   ❌ Download failed"
        return 1
    fi

    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 HOW TO USE THIS SCRIPT"
echo ""
echo "Option 1: Provide TikTok URLs directly"
echo "   Edit this file and add URLs to the TIKTOK_URLS array below"
echo ""
echo "Option 2: Use TikTok trending API"
echo "   Automatically fetch trending videos (requires API setup)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Example TikTok URLs (REPLACE THESE with real TikTok video URLs)
TIKTOK_URLS=(
    # Add your TikTok URLs here
    # Format: "URL|category"
    # Example:
    # "https://www.tiktok.com/@username/video/1234567890|sports"
    # "https://www.tiktok.com/@username/video/0987654321|comedy"
)

if [ ${#TIKTOK_URLS[@]} -eq 0 ]; then
    echo "⚠️  No TikTok URLs provided!"
    echo ""
    echo "To download TikTok videos, you need to:"
    echo ""
    echo "1. Find TikTok videos you want (browse TikTok on your phone/computer)"
    echo ""
    echo "2. Copy the video URL (Share → Copy Link)"
    echo ""
    echo "3. Add the URL to this script:"
    echo "   Edit: $0"
    echo "   Add to TIKTOK_URLS array:"
    echo ""
    echo "   TIKTOK_URLS=("
    echo "       \"https://www.tiktok.com/@user/video/123456|sports\""
    echo "       \"https://www.tiktok.com/@user/video/789012|comedy\""
    echo "   )"
    echo ""
    echo "4. Run this script again:"
    echo "   bash $0"
    echo ""
    exit 0
fi

# Download all videos
echo "📥 Downloading ${#TIKTOK_URLS[@]} TikTok videos..."
echo ""

downloaded_count=0
failed_count=0

for entry in "${TIKTOK_URLS[@]}"; do
    IFS='|' read -r url category <<< "$entry"

    if download_tiktok_video "$url" "$category"; then
        ((downloaded_count++))
    else
        ((failed_count++))
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Download Complete!"
echo ""
echo "   Downloaded: $downloaded_count"
echo "   Failed: $failed_count"
echo "   Location: $DOWNLOAD_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Ingest videos into platform:"
echo "   python3 backend/ingest_tiktok_videos.py"
echo ""
echo "2. Or use the API directly:"
echo "   curl -X POST http://localhost:8080/api/v1/videos/ingest-tiktok \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"video_dir\": \"./tiktok_videos\"}'"
echo ""
echo "3. Refresh your frontend to see new videos!"
echo ""
