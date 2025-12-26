Demo-sim: Simple CDN caching simulation

This demo contains three services wired with Docker Compose:

- origin: nginx serving a static site (port 8080)
- backend: FastAPI app providing `/api/content` (port 8080)
- cdn: nginx reverse proxy + cache in front of origin and backend (port 8080)

How to run

1. From the `demo-sim` directory build and start the services:

```bash
docker compose up -d --build
```

2. Open the CDN endpoint in your browser:

- CDN (simulated): http://localhost:8080
- Origin (direct): http://localhost:8080
- Backend (direct API): http://localhost:8080/api/content

What to observe

- Open the browser devtools (Network) and refresh the page served by the CDN at `http://localhost:8080`.
- The page's JavaScript fetches `/api/content` every 3 seconds. The CDN will add an `X-Cache-Status` header with values like `HIT` or `MISS` depending on caching.
- Refresh repeatedly and observe that API responses are cached for 10s by default (configured in the CDN). Static assets are cached longer by the origin.

Example curl checks

- Fetch headers through the CDN (shows X-Cache-Status):

```bash
curl -I http://localhost:8080/api/content
```

- Fetch directly from backend (bypass CDN):

```bash
curl -i http://localhost:8080/api/content
```

Notes and next steps

- This demo is intentionally small and easy to run for experimenting with cache rules and headers.
- You can tweak cache TTLs in `demo-sim/cdn/nginx.conf` or `demo-sim/backend/main.py` (Cache-Control headers) to observe how the CDN reacts.
- To simulate cache purging, you can change query parameters or add logic in the CDN config to bypass cache based on cookies/headers.

Quick cache lifecycle test

1. Start the demo:

```bash
docker compose up -d --build
```

2. Run the included test script (requires curl):

```bash
./test/test_cache.sh
```

The script will:
- Request `/api/slow-content` through the CDN (first request expected to be a MISS and slow)
- Immediately request again (should be a HIT and fast)
- Then request with `Cache-Control: no-cache` to bypass the cache

You can also curl manually to observe headers such as `X-Cache-Status` and `X-Cache-TTL`.

AV1 and playback notes
----------------------
- This demo stores uploaded files under `./storage/uploads` and exposes them via the origin at `/uploads/<filename>` so the CDN can cache them.
- For production we will transcode uploads to AV1 (for bandwidth savings). For the Beta demo we accept uploaded video files as-is and assume playback-capable browsers or pre-encoded AV1 sample files.
- Optional: to transcode to AV1 locally (requires ffmpeg with libaom or rav1e), run:

```bash
# Example ffmpeg command to encode to AV1 (may be slow locally):
ffmpeg -i input.mp4 -c:v libaom-av1 -crf 30 -b:v 0 -strict -2 out_av1.mp4
```

Frontend wiring
---------------
1. Upload a file to the backend using `POST /api/upload` (multipart form). The response contains `video_id` and `filename`.
2. Request `GET /api/playback/{video_id}` to receive a `playback_url` which points to `http://localhost:8080/uploads/<filename>` (served by CDN + origin).
3. Set the player source to that `playback_url`. For HLS we will later generate `index.m3u8` and segments; for now playback uses the uploaded file directly or pre-generated segments.
