#!/usr/bin/env bash
# Simple cache test script for demo-sim
# Usage: ./test_cache.sh

CDN=http://localhost:8001

echo "First request (expect MISS):"
curl -i "$CDN/api/slow-content"

echo -e "\nSecond request (immediate, expect HIT):"
curl -i "$CDN/api/slow-content"

echo -e "\nBypass cache (Cache-Control: no-cache):"
curl -i -H "Cache-Control: no-cache" "$CDN/api/slow-content"
