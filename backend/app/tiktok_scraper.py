"""
TikTok Video Scraper

Downloads TikTok videos and extracts metadata for ingestion into Clipstream.

Uses yt-dlp (the most reliable TikTok downloader) to:
- Download videos without watermark
- Extract metadata (title, creator, views, likes, etc.)
- Generate embeddings (placeholder for now)
- Upload to CDN or local storage
"""

import os
import json
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Video download settings
TIKTOK_DOWNLOAD_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
TIKTOK_OUTPUT_TEMPLATE = "%(id)s.%(ext)s"


class TikTokScraper:
    """
    TikTok video scraper using yt-dlp.

    Requires: pip install yt-dlp
    """

    def __init__(self, download_dir: str = "/tmp/tiktok_downloads"):
        """
        Initialize TikTok scraper.

        Args:
            download_dir: Directory to save downloaded videos
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_video(self, tiktok_url: str) -> Optional[Dict[str, Any]]:
        """
        Download a TikTok video and extract metadata.

        Args:
            tiktok_url: TikTok video URL (e.g., https://www.tiktok.com/@user/video/123...)

        Returns:
            dict: Video metadata and file path, or None if failed
            {
                "url": "original_tiktok_url",
                "video_path": "/path/to/downloaded/video.mp4",
                "title": "Video title",
                "creator": "username",
                "creator_name": "Display Name",
                "duration": 15.3,
                "view_count": 1234567,
                "like_count": 45678,
                "comment_count": 1234,
                "share_count": 567,
                "description": "Video description",
                "hashtags": ["funny", "viral"],
                "thumbnail": "thumbnail_url",
                "upload_date": "20231215",
            }
        """
        try:
            logger.info(f"Downloading TikTok video: {tiktok_url}")

            # Use yt-dlp to download and extract metadata
            output_path = self.download_dir / TIKTOK_OUTPUT_TEMPLATE

            # Run yt-dlp command
            cmd = [
                "yt-dlp",
                "--format", TIKTOK_DOWNLOAD_FORMAT,
                "--output", str(output_path),
                "--write-info-json",
                "--no-warnings",
                "--quiet",
                tiktok_url
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {stderr.decode()}")
                return None

            # Find the downloaded video file
            video_files = list(self.download_dir.glob("*.mp4"))
            if not video_files:
                logger.error("No video file found after download")
                return None

            video_path = video_files[-1]  # Most recent

            # Load metadata from info.json
            info_json_path = video_path.with_suffix(".info.json")
            if not info_json_path.exists():
                logger.warning("No metadata file found, using defaults")
                metadata = self._extract_basic_metadata(video_path, tiktok_url)
            else:
                with open(info_json_path, "r") as f:
                    info = json.load(f)
                metadata = self._parse_metadata(info, video_path, tiktok_url)

            logger.info(f"Successfully downloaded: {metadata['title']}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to download TikTok video: {e}")
            return None

    def _parse_metadata(self, info: dict, video_path: Path, original_url: str) -> Dict[str, Any]:
        """
        Parse yt-dlp metadata into Clipstream format.

        Args:
            info: yt-dlp info dict
            video_path: Path to downloaded video
            original_url: Original TikTok URL

        Returns:
            dict: Parsed metadata
        """
        # Extract hashtags from description
        description = info.get("description", "")
        hashtags = [tag.strip("#") for tag in description.split() if tag.startswith("#")]

        return {
            "url": original_url,
            "video_path": str(video_path),
            "title": info.get("title", "TikTok Video"),
            "creator": info.get("uploader_id", info.get("uploader", "unknown")),
            "creator_name": info.get("uploader", "Unknown Creator"),
            "duration": float(info.get("duration", 15.0)),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "comment_count": info.get("comment_count", 0),
            "share_count": info.get("repost_count", 0),
            "description": description,
            "hashtags": hashtags,
            "thumbnail": info.get("thumbnail", ""),
            "upload_date": info.get("upload_date", ""),
            "file_size": video_path.stat().st_size,
            "content_hash": self._compute_hash(video_path),
        }

    def _extract_basic_metadata(self, video_path: Path, original_url: str) -> Dict[str, Any]:
        """
        Extract basic metadata when info.json is not available.

        Args:
            video_path: Path to video file
            original_url: Original TikTok URL

        Returns:
            dict: Basic metadata
        """
        return {
            "url": original_url,
            "video_path": str(video_path),
            "title": f"TikTok Video - {video_path.stem}",
            "creator": "unknown",
            "creator_name": "Unknown Creator",
            "duration": 15.0,  # Default TikTok length
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "description": "",
            "hashtags": [],
            "thumbnail": "",
            "upload_date": "",
            "file_size": video_path.stat().st_size,
            "content_hash": self._compute_hash(video_path),
        }

    def _compute_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of video file.

        Args:
            file_path: Path to video file

        Returns:
            str: SHA256 hex digest
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def download_multiple(self, tiktok_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Download multiple TikTok videos concurrently.

        Args:
            tiktok_urls: List of TikTok URLs

        Returns:
            list: List of video metadata dicts (None for failed downloads)
        """
        tasks = [self.download_video(url) for url in tiktok_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Download task failed: {result}")
            elif result is not None:
                valid_results.append(result)

        return valid_results

    def cleanup(self):
        """
        Clean up downloaded files from temp directory.
        """
        try:
            import shutil
            if self.download_dir.exists():
                shutil.rmtree(self.download_dir)
                logger.info(f"Cleaned up download directory: {self.download_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup download directory: {e}")


async def download_and_prepare_tiktok_videos(
    tiktok_urls: List[str],
    upload_to_cdn: bool = False,
    cdn_bucket: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Download TikTok videos and prepare them for ingestion.

    Args:
        tiktok_urls: List of TikTok video URLs
        upload_to_cdn: Whether to upload to CDN (GCS)
        cdn_bucket: GCS bucket name (required if upload_to_cdn=True)

    Returns:
        list: List of video data ready for ingestion
    """
    scraper = TikTokScraper()

    try:
        # Download all videos
        downloaded_videos = await scraper.download_multiple(tiktok_urls)

        if not downloaded_videos:
            logger.warning("No videos were successfully downloaded")
            return []

        # Prepare for ingestion
        video_data_list = []

        for video in downloaded_videos:
            # Determine category from hashtags
            category = "general"
            if video["hashtags"]:
                # Use first hashtag as category
                category = video["hashtags"][0].lower()

            # Build ingestion data
            video_data = {
                "url": video["url"],  # Original TikTok URL
                "cdn_url": video["video_path"],  # Local path (or CDN URL after upload)
                "title": video["title"],
                "category": category,
                "duration": video["duration"],
                "creator_id": f"tiktok:{video['creator']}",
                "tags": video["hashtags"],
                "description": video["description"],
                "filename": Path(video["video_path"]).name,
                "file_size": video["file_size"],
                "content_hash": video["content_hash"],
                "status": "active",
                "embedding": [],  # TODO: Generate embeddings

                # TikTok-specific metadata
                "source": "tiktok",
                "source_metadata": {
                    "creator": video["creator"],
                    "creator_name": video["creator_name"],
                    "view_count": video["view_count"],
                    "like_count": video["like_count"],
                    "comment_count": video["comment_count"],
                    "share_count": video["share_count"],
                    "upload_date": video["upload_date"],
                }
            }

            # Upload to CDN if requested
            if upload_to_cdn and cdn_bucket:
                try:
                    from google.cloud import storage

                    client = storage.Client()
                    bucket = client.bucket(cdn_bucket)
                    blob_name = f"tiktok/{video['content_hash']}.mp4"
                    blob = bucket.blob(blob_name)

                    blob.upload_from_filename(video["video_path"])

                    # Update CDN URL
                    video_data["cdn_url"] = f"gs://{cdn_bucket}/{blob_name}"

                    logger.info(f"Uploaded to CDN: {blob_name}")
                except Exception as e:
                    logger.error(f"Failed to upload to CDN: {e}")

            video_data_list.append(video_data)

        logger.info(f"Prepared {len(video_data_list)} TikTok videos for ingestion")
        return video_data_list

    finally:
        # Cleanup temp files
        if not upload_to_cdn:
            # Keep files if not uploading to CDN
            logger.info("Keeping downloaded files (not uploaded to CDN)")
        else:
            scraper.cleanup()


# Example usage
async def main():
    """Example: Download TikTok videos and prepare for ingestion."""

    # Example TikTok URLs
    tiktok_urls = [
        "https://www.tiktok.com/@user/video/1234567890",
        "https://www.tiktok.com/@user/video/0987654321",
    ]

    # Download and prepare
    videos = await download_and_prepare_tiktok_videos(
        tiktok_urls=tiktok_urls,
        upload_to_cdn=False,  # Set to True for production with GCS
        cdn_bucket=None  # Set to your GCS bucket name
    )

    print(f"Downloaded {len(videos)} videos")
    for video in videos:
        print(f"  - {video['title']} ({video['duration']}s)")


if __name__ == "__main__":
    asyncio.run(main())
