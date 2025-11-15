from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class FollowUser(BaseModel):
    id: str
    username: str
    displayName: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    followerCount: int
    isFollowing: bool
    isVerified: Optional[bool] = False

class FollowRequest(BaseModel):
    user_id: str

@router.post("/follow")
async def follow_user(
    follow_request: FollowRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Follow a user
    """
    try:
        target_user_id = follow_request.user_id

        # Can't follow yourself
        if current_user_id == target_user_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")

        # Check if already following
        check_query = """
            SELECT * FROM follow
            WHERE follower_id = $follower_id
              AND following_id = $following_id
            LIMIT 1
        """
        check_result = await db_client.query(check_query, {
            'follower_id': current_user_id,
            'following_id': target_user_id
        })

        if check_result and len(check_result) > 0 and 'result' in check_result[0]:
            if len(check_result[0]['result']) > 0:
                raise HTTPException(status_code=400, detail="Already following this user")

        # Create follow relationship
        create_query = """
            CREATE follow CONTENT {
                follower_id: $follower_id,
                following_id: $following_id,
                createdAt: time::now()
            }
        """
        await db_client.query(create_query, {
            'follower_id': current_user_id,
            'following_id': target_user_id
        })

        # Create notification for the followed user
        notification_query = """
            CREATE notification CONTENT {
                type: 'follow',
                userId: $follower_id,
                content: 'started following you',
                targetUserId: $following_id,
                timestamp: time::now(),
                read: false
            }
        """
        await db_client.query(notification_query, {
            'follower_id': current_user_id,
            'following_id': target_user_id
        })

        return {"success": True, "message": "User followed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error following user: {e}")
        raise HTTPException(status_code=500, detail="Failed to follow user")

@router.post("/unfollow")
async def unfollow_user(
    follow_request: FollowRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Unfollow a user
    """
    try:
        target_user_id = follow_request.user_id

        # Delete follow relationship
        delete_query = """
            DELETE follow
            WHERE follower_id = $follower_id
              AND following_id = $following_id
        """
        await db_client.query(delete_query, {
            'follower_id': current_user_id,
            'following_id': target_user_id
        })

        return {"success": True, "message": "User unfollowed successfully"}
    except Exception as e:
        print(f"Error unfollowing user: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfollow user")

@router.get("/followers/{user_id}", response_model=List[FollowUser])
async def get_followers(
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user),
    limit: int = 50
):
    """
    Get all followers of a user
    """
    try:
        query = """
            SELECT follower_id FROM follow
            WHERE following_id = $user_id
            LIMIT $limit
        """

        result = await db_client.query(query, {
            'user_id': user_id,
            'limit': limit
        })

        followers = []
        if result and len(result) > 0 and 'result' in result[0]:
            for follow in result[0]['result']:
                follower_id = follow.get('follower_id')
                if not follower_id:
                    continue

                # Get follower user details
                user = await db_client.get_user_by_id(follower_id)
                if not user:
                    continue

                # Get follower count for this user
                follower_count_query = """
                    SELECT count() as count FROM follow
                    WHERE following_id = $user_id
                    GROUP ALL
                """
                follower_count_result = await db_client.query(follower_count_query, {'user_id': follower_id})
                follower_count = 0
                if follower_count_result and len(follower_count_result) > 0 and 'result' in follower_count_result[0]:
                    res = follower_count_result[0]['result']
                    if res:
                        follower_count = res[0].get('count', 0)

                # Check if current user is following this follower
                is_following = False
                if current_user_id and current_user_id != follower_id:
                    follow_check_query = """
                        SELECT * FROM follow
                        WHERE follower_id = $current_user_id
                          AND following_id = $target_id
                        LIMIT 1
                    """
                    follow_check_result = await db_client.query(follow_check_query, {
                        'current_user_id': current_user_id,
                        'target_id': follower_id
                    })
                    if follow_check_result and len(follow_check_result) > 0 and 'result' in follow_check_result[0]:
                        is_following = len(follow_check_result[0]['result']) > 0

                followers.append(FollowUser(
                    id=str(user.get('id', '')),
                    username=user.get('username', ''),
                    displayName=user.get('display_name', ''),
                    avatar=user.get('avatar'),
                    bio=user.get('bio'),
                    followerCount=follower_count,
                    isFollowing=is_following,
                    isVerified=user.get('isVerified', False)
                ))

        return followers
    except Exception as e:
        print(f"Error fetching followers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch followers")

@router.get("/following/{user_id}", response_model=List[FollowUser])
async def get_following(
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user),
    limit: int = 50
):
    """
    Get all users that a user is following
    """
    try:
        query = """
            SELECT following_id FROM follow
            WHERE follower_id = $user_id
            LIMIT $limit
        """

        result = await db_client.query(query, {
            'user_id': user_id,
            'limit': limit
        })

        following = []
        if result and len(result) > 0 and 'result' in result[0]:
            for follow in result[0]['result']:
                following_id = follow.get('following_id')
                if not following_id:
                    continue

                # Get following user details
                user = await db_client.get_user_by_id(following_id)
                if not user:
                    continue

                # Get follower count for this user
                follower_count_query = """
                    SELECT count() as count FROM follow
                    WHERE following_id = $user_id
                    GROUP ALL
                """
                follower_count_result = await db_client.query(follower_count_query, {'user_id': following_id})
                follower_count = 0
                if follower_count_result and len(follower_count_result) > 0 and 'result' in follower_count_result[0]:
                    res = follower_count_result[0]['result']
                    if res:
                        follower_count = res[0].get('count', 0)

                # Check if current user is following this user
                is_following = False
                if current_user_id and current_user_id != following_id:
                    follow_check_query = """
                        SELECT * FROM follow
                        WHERE follower_id = $current_user_id
                          AND following_id = $target_id
                        LIMIT 1
                    """
                    follow_check_result = await db_client.query(follow_check_query, {
                        'current_user_id': current_user_id,
                        'target_id': following_id
                    })
                    if follow_check_result and len(follow_check_result) > 0 and 'result' in follow_check_result[0]:
                        is_following = len(follow_check_result[0]['result']) > 0

                following.append(FollowUser(
                    id=str(user.get('id', '')),
                    username=user.get('username', ''),
                    displayName=user.get('display_name', ''),
                    avatar=user.get('avatar'),
                    bio=user.get('bio'),
                    followerCount=follower_count,
                    isFollowing=is_following,
                    isVerified=user.get('isVerified', False)
                ))

        return following
    except Exception as e:
        print(f"Error fetching following: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch following")

@router.get("/is-following/{user_id}")
async def check_is_following(
    user_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Check if current user is following a specific user
    """
    try:
        query = """
            SELECT * FROM follow
            WHERE follower_id = $follower_id
              AND following_id = $following_id
            LIMIT 1
        """

        result = await db_client.query(query, {
            'follower_id': current_user_id,
            'following_id': user_id
        })

        is_following = False
        if result and len(result) > 0 and 'result' in result[0]:
            is_following = len(result[0]['result']) > 0

        return {"isFollowing": is_following}
    except Exception as e:
        print(f"Error checking follow status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check follow status")
