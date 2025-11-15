from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class Sound(BaseModel):
    id: str
    title: str
    artist: str
    duration: int
    coverArt: Optional[str] = None
    audioUrl: str
    category: str
    isPopular: bool
    usageCount: int
    isFavorite: Optional[bool] = False

@router.get("", response_model=List[Sound])
async def get_sounds(
    category: str = Query("trending"),
    current_user_id: str = Depends(get_current_user),
    limit: int = 50
):
    """Get sounds by category"""
    try:
        if category == "trending":
            query = """
                SELECT * FROM sound
                WHERE isPopular = true
                ORDER BY usageCount DESC
                LIMIT $limit
            """
        elif category == "favorites":
            query = """
                SELECT sound.* FROM favorite_sound
                INNER JOIN sound ON favorite_sound.soundId = sound.id
                WHERE favorite_sound.userId = $user_id
                LIMIT $limit
            """
        else:
            query = """
                SELECT * FROM sound
                WHERE category = $category
                ORDER BY usageCount DESC
                LIMIT $limit
            """

        result = await db_client.query(query, {
            'category': category,
            'user_id': current_user_id,
            'limit': limit
        })

        sounds = []
        if result and len(result) > 0 and 'result' in result[0]:
            for sound in result[0]['result']:
                # Check if user has favorited this sound
                fav_query = """
                    SELECT * FROM favorite_sound
                    WHERE userId = $user_id AND soundId = $sound_id
                    LIMIT 1
                """

                fav_result = await db_client.query(fav_query, {
                    'user_id': current_user_id,
                    'sound_id': str(sound.get('id', ''))
                })

                is_favorite = False
                if fav_result and len(fav_result) > 0 and 'result' in fav_result[0]:
                    is_favorite = len(fav_result[0]['result']) > 0

                sounds.append(Sound(
                    id=str(sound.get('id', '')),
                    title=sound.get('title', ''),
                    artist=sound.get('artist', ''),
                    duration=sound.get('duration', 0),
                    coverArt=sound.get('coverArt'),
                    audioUrl=sound.get('audioUrl', ''),
                    category=sound.get('category', ''),
                    isPopular=sound.get('isPopular', False),
                    usageCount=sound.get('usageCount', 0),
                    isFavorite=is_favorite
                ))

        return sounds
    except Exception as e:
        print(f"Error fetching sounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sounds")

@router.get("/search", response_model=List[Sound])
async def search_sounds(
    q: str = Query(..., min_length=2),
    current_user_id: str = Depends(get_current_user),
    limit: int = 50
):
    """Search sounds"""
    try:
        search_term = f"%{q.lower()}%"

        query = """
            SELECT * FROM sound
            WHERE string::lowercase(title) LIKE $search
               OR string::lowercase(artist) LIKE $search
            ORDER BY usageCount DESC
            LIMIT $limit
        """

        result = await db_client.query(query, {
            'search': search_term,
            'limit': limit
        })

        sounds = []
        if result and len(result) > 0 and 'result' in result[0]:
            for sound in result[0]['result']:
                # Check if user has favorited this sound
                fav_query = """
                    SELECT * FROM favorite_sound
                    WHERE userId = $user_id AND soundId = $sound_id
                    LIMIT 1
                """

                fav_result = await db_client.query(fav_query, {
                    'user_id': current_user_id,
                    'sound_id': str(sound.get('id', ''))
                })

                is_favorite = False
                if fav_result and len(fav_result) > 0 and 'result' in fav_result[0]:
                    is_favorite = len(fav_result[0]['result']) > 0

                sounds.append(Sound(
                    id=str(sound.get('id', '')),
                    title=sound.get('title', ''),
                    artist=sound.get('artist', ''),
                    duration=sound.get('duration', 0),
                    coverArt=sound.get('coverArt'),
                    audioUrl=sound.get('audioUrl', ''),
                    category=sound.get('category', ''),
                    isPopular=sound.get('isPopular', False),
                    usageCount=sound.get('usageCount', 0),
                    isFavorite=is_favorite
                ))

        return sounds
    except Exception as e:
        print(f"Error searching sounds: {e}")
        raise HTTPException(status_code=500, detail="Failed to search sounds")

@router.post("/{sound_id}/favorite", status_code=201)
async def favorite_sound(
    sound_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Favorite a sound"""
    try:
        query = """
            CREATE favorite_sound CONTENT {
                userId: $user_id,
                soundId: $sound_id,
                createdAt: time::now()
            }
        """

        await db_client.query(query, {
            'user_id': current_user_id,
            'sound_id': sound_id
        })

        return {"success": True, "message": "Sound favorited"}
    except Exception as e:
        print(f"Error favoriting sound: {e}")
        raise HTTPException(status_code=500, detail="Failed to favorite sound")

@router.delete("/{sound_id}/favorite")
async def unfavorite_sound(
    sound_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Unfavorite a sound"""
    try:
        query = """
            DELETE favorite_sound
            WHERE userId = $user_id AND soundId = $sound_id
        """

        await db_client.query(query, {
            'user_id': current_user_id,
            'sound_id': sound_id
        })

        return {"success": True, "message": "Sound unfavorited"}
    except Exception as e:
        print(f"Error unfavoriting sound: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfavorite sound")
