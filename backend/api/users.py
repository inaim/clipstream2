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
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[str] = None
    watch_tokens: int = 0                # $WATCH contribution points (determines creator's revenue share)
    watch_contribution_pending: int = 0  # points earned, awaiting TrustedCrypto settlement

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """
    Get user profile by user_id.
    This endpoint is public for now - in production you might want to add authentication.
    """
    print(f"[DEBUG] get_user_profile called with user_id: {user_id}")
    try:
        user = await db_client.get_user_by_id(user_id)

        # If the profile does not exist (common in local dev without auth setup),
        # return a lightweight placeholder so the frontend can render instead of
        # getting stuck on "Loading profile...".
        if not user:
            return UserProfile(
                user_id=str(user_id),
                email="",
                display_name="Guest",
                username=str(user_id).split(":")[-1] if ":" in str(user_id) else str(user_id),
                avatar_url=None,
                bio=None,
                created_at=None,
                watch_tokens=0,
                watch_contribution_pending=0,
            )

        # Extract user_id from the RecordID
        user_id_str = str(user.get('id', user_id))

        return UserProfile(
            user_id=user_id_str,
            email=user.get('email', ''),
            display_name=user.get('display_name'),
            username=user.get('username'),
            avatar_url=user.get('avatar_url'),
            bio=user.get('bio'),
            created_at=user.get('created_at'),
            watch_tokens=user.get('watch_tokens', 0),
            watch_contribution_pending=user.get('watch_contribution_pending', 0)
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
