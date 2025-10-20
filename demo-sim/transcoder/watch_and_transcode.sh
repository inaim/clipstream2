#!/usr/bin/env bash
set -euo pipefail

UPLOADS_DIR=/work/storage/uploads
BACKEND_URL=${BACKEND_URL:-http://backend:8000}

echo "Transcoder starting. Watching $UPLOADS_DIR for .todo files"

# Ensure uploads dir exists
mkdir -p "$UPLOADS_DIR"

while true; do
  for todo in "$UPLOADS_DIR"/*.todo; do
    [ -e "$todo" ] || continue
    base=$(basename "$todo" .todo)
    src="$UPLOADS_DIR/$base"
    # If source file doesn't exist yet, skip
    if [ ! -f "$src" ]; then
      echo "Source $src not found, removing marker $todo" 
      rm -f "$todo"
      continue
    fi

    outmp4="$UPLOADS_DIR/${base%.*}.transcoded.mp4"
    echo "Transcoding $src -> $outmp4"

    # Transcode to a reasonably compatible MP4 (H.264) for demo playback
    ffmpeg -y -i "$src" -c:v libx264 -preset veryfast -crf 28 -c:a aac -b:a 128k "$outmp4"

    if [ -f "$outmp4" ]; then
      echo "Transcode complete: $outmp4"
      # Notify backend (container name 'backend' is available in docker-compose network)
      # Send JSON with filename mapping: original filename -> transcoded filename
      json=$(jq -n --arg orig "$base" --arg out "$(basename "$outmp4")" '{original: $orig, transcoded: $out}')
      # Try to call backend endpoint; tolerate failures
      curl -s -X POST "$BACKEND_URL/api/transcode_complete" -H "Content-Type: application/json" -d "$json" || true
      # mark done and remove todo marker
      mv "$todo" "$todo.done"
    else
      echo "Transcode failed for $src"
    fi
  done
  sleep 2
done
