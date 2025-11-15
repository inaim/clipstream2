from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class SearchResult(BaseModel):
    type: str  # 'user', 'video', 'hashtag', 'sound'
    id: str
    title: str
    subtitle: Optional[str] = None
    thumbnail: Optional[str] = None
    avatar: Optional[str] = None
    stats: Optional[Dict[str, int]] = None

class TrendingHashtag(BaseModel):
    id: str
    name: str
    videoCount: int
    viewCount: int
    isNew: Optional[bool] = False

class TrendingSound(BaseModel):
    id: str
    title: str
    artist: str
    videoCount: int
    thumbnail: Optional[str] = None

class TrendingCreator(BaseModel):
    id: str
    username: str
    displayName: str
    avatar: Optional[str] = None
    followerCount: int
    isVerified: Optional[bool] = False

@router.get("/search", response_model=List[SearchResult])
async def universal_search(
    q: str = Query(..., min_length=2),
    current_user_id: str = Depends(get_current_user)
):
    """Universal search across users, videos, hashtags, and sounds"""
    try:
        results = []
        search_term = f"%{q.lower()}%"

        # Search users
        user_query = """
            SELECT * FROM user
            WHERE string::lowercase(username) LIKE $search
               OR string::lowercase(display_name) LIKE $search
            LIMIT 10
        """

        user_result = await db_client.query(user_query, {'search': search_term})

        if user_result and len(user_result) > 0 and 'result' in user_result[0]:
            for user in user_result[0]['result']:
                # Get follower count
                follower_query = """
                    SELECT count() as count FROM follow
                    WHERE following_id = $user_id
                    GROUP ALL
                """
                follower_result = await db_client.query(follower_query, {'user_id': str(user.get('id', ''))})
                follower_count = 0
                if follower_result and len(follower_result) > 0 and 'result' in follower_result[0]:
                    res = follower_result[0]['result']
                    if res:
                        follower_count = res[0].get('count', 0)

                results.append(SearchResult(
                    type='user',
                    id=str(user.get('id', '')),
                    title=user.get('display_name', ''),
                    subtitle=user.get('username', ''),
                    avatar=user.get('avatar'),
                    stats={'followers': follower_count}
                ))

        # Search videos
        video_query = """
            SELECT * FROM video
            WHERE string::lowercase(title) LIKE $search
               OR string::lowercase(description) LIKE $search
            LIMIT 10
        """

        video_result = await db_client.query(video_query, {'search': search_term})

        if video_result and len(video_result) > 0 and 'result' in video_result[0]:
            for video in video_result[0]['result']:
                # Get creator username
                creator = await db_client.get_user_by_id(video.get('user_id', ''))
                creator_username = creator.get('username', '') if creator else ''

                results.append(SearchResult(
                    type='video',
                    id=str(video.get('id', '')),
                    title=video.get('title', ''),
                    subtitle=f"@{creator_username}",
                    thumbnail=video.get('thumbnail_url'),
                    stats={
                        'views': video.get('views', 0),
                        'likes': video.get('likes', 0)
                    }
                ))

        # Search hashtags
        hashtag_query = """
            SELECT
                name,
                count() as videoCount
            FROM hashtag
            WHERE string::lowercase(name) LIKE $search
            GROUP BY name
            LIMIT 10
        """

        hashtag_result = await db_client.query(hashtag_query, {'search': search_term})

        if hashtag_result and len(hashtag_result) > 0 and 'result' in hashtag_result[0]:
            for hashtag in hashtag_result[0]['result']:
                results.append(SearchResult(
                    type='hashtag',
                    id=f"hashtag_{hashtag.get('name', '')}",
                    title=hashtag.get('name', ''),
                    stats={'videos': hashtag.get('videoCount', 0)}
                ))

        # Search sounds
        sound_query = """
            SELECT * FROM sound
            WHERE string::lowercase(title) LIKE $search
               OR string::lowercase(artist) LIKE $search
            LIMIT 10
        """

        sound_result = await db_client.query(sound_query, {'search': search_term})

        if sound_result and len(sound_result) > 0 and 'result' in sound_result[0]:
            for sound in sound_result[0]['result']:
                results.append(SearchResult(
                    type='sound',
                    id=str(sound.get('id', '')),
                    title=sound.get('title', ''),
                    subtitle=sound.get('artist', ''),
                    stats={'videos': sound.get('usageCount', 0)}
                ))

        return results
    except Exception as e:
        print(f"Error in universal search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/trending/hashtags", response_model=List[TrendingHashtag])
async def get_trending_hashtags(limit: int = 20):
    """Get trending hashtags"""
    try:
        query = """
            SELECT
                name,
                count() as videoCount,
                sum(views) as totalViews
            FROM hashtag
            GROUP BY name
            ORDER BY totalViews DESC, videoCount DESC
            LIMIT $limit
        """

        result = await db_client.query(query, {'limit': limit})

        hashtags = []
        if result and len(result) > 0 and 'result' in result[0]:
            for hashtag in result[0]['result']:
                hashtags.append(TrendingHashtag(
                    id=f"hashtag_{hashtag.get('name', '')}",
                    name=hashtag.get('name', ''),
                    videoCount=hashtag.get('videoCount', 0),
                    viewCount=hashtag.get('totalViews', 0),
                    isNew=False  # You could add logic to determine if it's new
                ))

        return hashtags
    except Exception as e:
        print(f"Error fetching trending hashtags: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending hashtags")

@router.get("/trending/sounds", response_model=List[TrendingSound])
async def get_trending_sounds(limit: int = 20):
    """Get trending sounds"""
    try:
        query = """
            SELECT * FROM sound
            ORDER BY usageCount DESC
            LIMIT $limit
        """

        result = await db_client.query(query, {'limit': limit})

        sounds = []
        if result and len(result) > 0 and 'result' in result[0]:
            for sound in result[0]['result']:
                sounds.append(TrendingSound(
                    id=str(sound.get('id', '')),
                    title=sound.get('title', ''),
                    artist=sound.get('artist', ''),
                    videoCount=sound.get('usageCount', 0),
                    thumbnail=sound.get('coverArt')
                ))

        return sounds
    except Exception as e:
        print(f"Error fetching trending sounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending sounds")

@router.get("/trending/creators", response_model=List[TrendingCreator])
async def get_trending_creators(limit: int = 20):
    """Get trending creators"""
    try:
        # Get users with most followers
        query = """
            SELECT
                following_id as userId,
                count() as followerCount
            FROM follow
            GROUP BY following_id
            ORDER BY followerCount DESC
            LIMIT $limit
        """

        result = await db_client.query(query, {'limit': limit})

        creators = []
        if result and len(result) > 0 and 'result' in result[0]:
            for item in result[0]['result']:
                user = await db_client.get_user_by_id(item.get('userId', ''))
                if user:
                    creators.append(TrendingCreator(
                        id=str(user.get('id', '')),
                        username=user.get('username', ''),
                        displayName=user.get('display_name', ''),
                        avatar=user.get('avatar'),
                        followerCount=item.get('followerCount', 0),
                        isVerified=user.get('isVerified', False)
                    ))

        return creators
    except Exception as e:
        print(f"Error fetching trending creators: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending creators")
