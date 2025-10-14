from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class UserProfile(BaseModel):
    user_id: str
    email: str
    display_name: Optional[str] = None
    watch_tokens: int = 0
    watch_tokens_pending: int = 0

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """
    Get user profile by user_id.
    This endpoint is public for now - in production you might want to add authentication.
    """
    try:
        user = await db_client.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Extract user_id from the RecordID
        user_id_str = str(user.get('id', user_id))
        
        return UserProfile(
            user_id=user_id_str,
            email=user.get('email', ''),
            display_name=user.get('display_name'),
            watch_tokens=user.get('watch_tokens', 0),
            watch_tokens_pending=user.get('watch_tokens_pending', 0)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user_id: str = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    Requires authentication.
    """
    return await get_user_profile(current_user_id)

