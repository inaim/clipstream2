from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class UserInterests(BaseModel):
    interests: List[str]

class UserInterestsResponse(BaseModel):
    hasInterests: bool
    interests: List[str]

@router.get("/{user_id}/interests", response_model=UserInterestsResponse)
async def get_user_interests(user_id: str):
    """Get user's interests"""
    try:
        query = """
            SELECT interests FROM user
            WHERE id = $user_id
        """

        result = await db_client.query(query, {'user_id': user_id})

        interests = []
        has_interests = False

        if result and len(result) > 0 and 'result' in result[0]:
            users = result[0]['result']
            if users:
                user_interests = users[0].get('interests', [])
                if user_interests and len(user_interests) > 0:
                    interests = user_interests
                    has_interests = True

        return UserInterestsResponse(
            hasInterests=has_interests,
            interests=interests
        )
    except Exception as e:
        print(f"Error fetching user interests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user interests")

@router.post("/{user_id}/interests")
async def update_user_interests(
    user_id: str,
    interests_data: UserInterests,
    current_user_id: str = Depends(get_current_user)
):
    """Update user's interests"""
    try:
        # Verify user is updating their own interests
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Cannot update another user's interests")

        query = """
            UPDATE $user_id SET interests = $interests
        """

        await db_client.query(query, {
            'user_id': user_id,
            'interests': interests_data.interests
        })

        return {"success": True, "message": "Interests updated"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user interests: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user interests")
