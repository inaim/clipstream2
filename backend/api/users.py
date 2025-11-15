from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    watch_tokens: int = 0
    watch_tokens_pending: int = 0
    videoCount: int = 0
    followerCount: int = 0
    followingCount: int = 0
    totalLikes: int = 0
    totalViews: int = 0
    isFollowing: Optional[bool] = False
    isVerified: Optional[bool] = False

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None

class VideoItem(BaseModel):
    id: str
    title: str
    thumbnail_url: Optional[str] = None
    views: int
    likes: int
    uploadedAt: str
    status: str

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    current_user_id: Optional[str] = Depends(get_current_user)
):
    """
    Get complete user profile by user_id with all stats.
    """
    print(f"[DEBUG] get_user_profile called with user_id: {user_id}")
    try:
        user = await db_client.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id_str = str(user.get('id', user_id))

        # Get video count
        video_count_query = """
            SELECT count() as count FROM video
            WHERE user_id = $user_id
            GROUP ALL
        """
        video_count_result = await db_client.query(video_count_query, {'user_id': user_id_str})
        video_count = 0
        if video_count_result and len(video_count_result) > 0 and 'result' in video_count_result[0]:
            res = video_count_result[0]['result']
            if res:
                video_count = res[0].get('count', 0)

        # Get follower count
        follower_count_query = """
            SELECT count() as count FROM follow
            WHERE following_id = $user_id
            GROUP ALL
        """
        follower_count_result = await db_client.query(follower_count_query, {'user_id': user_id_str})
        follower_count = 0
        if follower_count_result and len(follower_count_result) > 0 and 'result' in follower_count_result[0]:
            res = follower_count_result[0]['result']
            if res:
                follower_count = res[0].get('count', 0)

        # Get following count
        following_count_query = """
            SELECT count() as count FROM follow
            WHERE follower_id = $user_id
            GROUP ALL
        """
        following_count_result = await db_client.query(following_count_query, {'user_id': user_id_str})
        following_count = 0
        if following_count_result and len(following_count_result) > 0 and 'result' in following_count_result[0]:
            res = following_count_result[0]['result']
            if res:
                following_count = res[0].get('count', 0)

        # Get total views
        total_views_query = """
            SELECT sum(views) as total FROM video
            WHERE user_id = $user_id
            GROUP ALL
        """
        total_views_result = await db_client.query(total_views_query, {'user_id': user_id_str})
        total_views = 0
        if total_views_result and len(total_views_result) > 0 and 'result' in total_views_result[0]:
            res = total_views_result[0]['result']
            if res:
                total_views = res[0].get('total', 0) or 0

        # Get total likes
        total_likes_query = """
            SELECT count() as count FROM like
            INNER JOIN video ON like.videoId = video.id
            WHERE video.user_id = $user_id
            GROUP ALL
        """
        total_likes_result = await db_client.query(total_likes_query, {'user_id': user_id_str})
        total_likes = 0
        if total_likes_result and len(total_likes_result) > 0 and 'result' in total_likes_result[0]:
            res = total_likes_result[0]['result']
            if res:
                total_likes = res[0].get('count', 0)

        # Check if current user is following this user
        is_following = False
        if current_user_id and current_user_id != user_id_str:
            follow_check_query = """
                SELECT * FROM follow
                WHERE follower_id = $current_user_id
                  AND following_id = $user_id
                LIMIT 1
            """
            follow_check_result = await db_client.query(follow_check_query, {
                'current_user_id': current_user_id,
                'user_id': user_id_str
            })
            if follow_check_result and len(follow_check_result) > 0 and 'result' in follow_check_result[0]:
                is_following = len(follow_check_result[0]['result']) > 0

        return UserProfile(
            user_id=user_id_str,
            username=user.get('username', ''),
            email=user.get('email', ''),
            display_name=user.get('display_name'),
            avatar=user.get('avatar'),
            bio=user.get('bio'),
            watch_tokens=user.get('watch_tokens', 0),
            watch_tokens_pending=user.get('watch_tokens_pending', 0),
            videoCount=video_count,
            followerCount=follower_count,
            followingCount=following_count,
            totalLikes=total_likes,
            totalViews=total_views,
            isFollowing=is_following,
            isVerified=user.get('isVerified', False)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

@router.get("/me/profile", response_model=UserProfile)
async def get_current_user_profile(current_user_id: str = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    Requires authentication.
    """
    return await get_user_profile(current_user_id, current_user_id)

@router.put("/{user_id}/profile")
async def update_user_profile(
    user_id: str,
    profile_data: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Update user profile.
    Users can only update their own profile.
    """
    try:
        # Verify user is updating their own profile
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Cannot update another user's profile")

        # Build update query dynamically based on provided fields
        updates = []
        params = {'user_id': user_id}

        if profile_data.display_name is not None:
            updates.append("display_name = $display_name")
            params['display_name'] = profile_data.display_name

        if profile_data.username is not None:
            # Check if username is already taken
            username_check_query = """
                SELECT * FROM user
                WHERE username = $username AND id != $user_id
                LIMIT 1
            """
            username_check_result = await db_client.query(username_check_query, {
                'username': profile_data.username,
                'user_id': user_id
            })
            if username_check_result and len(username_check_result) > 0 and 'result' in username_check_result[0]:
                if len(username_check_result[0]['result']) > 0:
                    raise HTTPException(status_code=400, detail="Username already taken")

            updates.append("username = $username")
            params['username'] = profile_data.username

        if profile_data.bio is not None:
            updates.append("bio = $bio")
            params['bio'] = profile_data.bio

        if profile_data.avatar is not None:
            updates.append("avatar = $avatar")
            params['avatar'] = profile_data.avatar

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        query = f"UPDATE $user_id SET {', '.join(updates)}"
        await db_client.query(query, params)

        return {"success": True, "message": "Profile updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@router.get("/{user_id}/videos", response_model=List[VideoItem])
async def get_user_videos(user_id: str, limit: int = 30):
    """
    Get all videos for a user.
    """
    try:
        query = """
            SELECT * FROM video
            WHERE user_id = $user_id
            ORDER BY uploadedAt DESC
            LIMIT $limit
        """

        result = await db_client.query(query, {
            'user_id': user_id,
            'limit': limit
        })

        videos = []
        if result and len(result) > 0 and 'result' in result[0]:
            for video in result[0]['result']:
                videos.append(VideoItem(
                    id=str(video.get('id', '')),
                    title=video.get('title', ''),
                    thumbnail_url=video.get('thumbnail_url'),
                    views=video.get('views', 0),
                    likes=video.get('likes', 0),
                    uploadedAt=video.get('uploadedAt', ''),
                    status=video.get('status', 'active')
                ))

        return videos
    except Exception as e:
        print(f"Error fetching user videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user videos")
