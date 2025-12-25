import asyncio
from app.tiktok_scraper import download_and_prepare_tiktok_videos
from app.ingestion_engine import ingest_initial_videos
from db.surrealdb_client import db_client

async def ingest_tiktok_videos():
    # Connect to database
    await db_client.connect()
    async_db = getattr(db_client, "async_db")

    # TikTok URLs to download
    tiktok_urls = [
        "https://www.tiktok.com/@nike/video/7305827482847587630",
        "https://www.tiktok.com/@gordonramsayofficial/video/7305827383847587630",
        "https://www.tiktok.com/@natgeo/video/7305827282847587630",
    ]

    # Download and prepare
    from app.tiktok_scraper import download_and_prepare_tiktok_videos
    videos = await download_and_prepare_tiktok_videos(tiktok_urls)

    # Ingest into database
    result = await ingest_initial_videos(async_db, videos)
    print(f"Ingested {result['ingested']} TikTok videos")

if __name__ == "__main__":
    asyncio.run(ingest_tiktok_videos())
