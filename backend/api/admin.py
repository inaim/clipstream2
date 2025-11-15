from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, timedelta
from db.surrealdb_client import db_client
from utils.auth import get_current_user
import csv
import io

router = APIRouter()

class AdminStats(BaseModel):
    totalUsers: int
    activeUsers: int
    totalVideos: int
    totalViews: int
    totalLikes: int
    flaggedContent: int
    revenue: float
    growthRate: float

class AdminUser(BaseModel):
    id: str
    username: str
    email: str
    displayName: str
    avatar: Optional[str] = None
    createdAt: str
    status: Literal['active', 'suspended', 'banned']
    videoCount: int
    followerCount: int
    totalViews: int
    totalLikes: int
    lastActive: str

class AdminVideo(BaseModel):
    id: str
    title: str
    creatorId: str
    creatorUsername: str
    uploadedAt: str
    status: Literal['active', 'processing', 'flagged', 'removed']
    views: int
    likes: int
    comments: int
    shares: int
    duration: int
    flagCount: int

# Dependency to check if user is admin
async def verify_admin(current_user_id: str = Depends(get_current_user)) -> str:
    """Verify that the current user is an admin"""
    user = await db_client.get_user_by_id(current_user_id)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user_id

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(current_user_id: str = Depends(verify_admin)):
    """Get admin dashboard statistics"""
    try:
        # Get total users
        user_count_query = "SELECT count() as count FROM user GROUP ALL"
        user_result = await db_client.query(user_count_query, {})
        total_users = 0
        if user_result and len(user_result) > 0 and 'result' in user_result[0]:
            res = user_result[0]['result']
            if res:
                total_users = res[0].get('count', 0)

        # Get active users (logged in within last 7 days)
        active_query = """
            SELECT count() as count FROM user
            WHERE lastActive > time::now() - 7d
            GROUP ALL
        """
        active_result = await db_client.query(active_query, {})
        active_users = 0
        if active_result and len(active_result) > 0 and 'result' in active_result[0]:
            res = active_result[0]['result']
            if res:
                active_users = res[0].get('count', 0)

        # Get total videos
        video_count_query = "SELECT count() as count FROM video GROUP ALL"
        video_result = await db_client.query(video_count_query, {})
        total_videos = 0
        if video_result and len(video_result) > 0 and 'result' in video_result[0]:
            res = video_result[0]['result']
            if res:
                total_videos = res[0].get('count', 0)

        # Get total views
        views_query = "SELECT sum(views) as total FROM video GROUP ALL"
        views_result = await db_client.query(views_query, {})
        total_views = 0
        if views_result and len(views_result) > 0 and 'result' in views_result[0]:
            res = views_result[0]['result']
            if res:
                total_views = res[0].get('total', 0)

        # Get total likes
        likes_query = "SELECT count() as count FROM like GROUP ALL"
        likes_result = await db_client.query(likes_query, {})
        total_likes = 0
        if likes_result and len(likes_result) > 0 and 'result' in likes_result[0]:
            res = likes_result[0]['result']
            if res:
                total_likes = res[0].get('count', 0)

        # Get flagged content count
        flagged_query = """
            SELECT count() as count FROM video
            WHERE status = 'flagged'
            GROUP ALL
        """
        flagged_result = await db_client.query(flagged_query, {})
        flagged_content = 0
        if flagged_result and len(flagged_result) > 0 and 'result' in flagged_result[0]:
            res = flagged_result[0]['result']
            if res:
                flagged_content = res[0].get('count', 0)

        # Calculate growth rate (new users in last 30 days vs previous 30 days)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)

        growth_rate = 0.0  # Placeholder

        return AdminStats(
            totalUsers=total_users,
            activeUsers=active_users,
            totalVideos=total_videos,
            totalViews=total_views,
            totalLikes=total_likes,
            flaggedContent=flagged_content,
            revenue=0.0,  # Placeholder - implement based on your monetization system
            growthRate=growth_rate
        )
    except Exception as e:
        print(f"Error fetching admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin stats")

@router.get("/users", response_model=List[AdminUser])
async def get_admin_users(
    current_user_id: str = Depends(verify_admin),
    limit: int = 100,
    offset: int = 0
):
    """Get all users for admin dashboard"""
    try:
        query = """
            SELECT * FROM user
            ORDER BY createdAt DESC
            LIMIT $limit
            START $offset
        """

        result = await db_client.query(query, {'limit': limit, 'offset': offset})

        users = []
        if result and len(result) > 0 and 'result' in result[0]:
            for user in result[0]['result']:
                user_id = str(user.get('id', ''))

                # Get video count
                video_count_query = """
                    SELECT count() as count FROM video
                    WHERE user_id = $user_id
                    GROUP ALL
                """
                video_count_result = await db_client.query(video_count_query, {'user_id': user_id})
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
                follower_count_result = await db_client.query(follower_count_query, {'user_id': user_id})
                follower_count = 0
                if follower_count_result and len(follower_count_result) > 0 and 'result' in follower_count_result[0]:
                    res = follower_count_result[0]['result']
                    if res:
                        follower_count = res[0].get('count', 0)

                # Get total views
                views_query = """
                    SELECT sum(views) as total FROM video
                    WHERE user_id = $user_id
                    GROUP ALL
                """
                views_result = await db_client.query(views_query, {'user_id': user_id})
                total_views = 0
                if views_result and len(views_result) > 0 and 'result' in views_result[0]:
                    res = views_result[0]['result']
                    if res:
                        total_views = res[0].get('total', 0)

                # Get total likes
                likes_query = """
                    SELECT count() as count FROM like
                    INNER JOIN video ON like.videoId = video.id
                    WHERE video.user_id = $user_id
                    GROUP ALL
                """
                likes_result = await db_client.query(likes_query, {'user_id': user_id})
                total_likes = 0
                if likes_result and len(likes_result) > 0 and 'result' in likes_result[0]:
                    res = likes_result[0]['result']
                    if res:
                        total_likes = res[0].get('count', 0)

                users.append(AdminUser(
                    id=user_id,
                    username=user.get('username', ''),
                    email=user.get('email', ''),
                    displayName=user.get('display_name', ''),
                    avatar=user.get('avatar'),
                    createdAt=user.get('createdAt', datetime.utcnow().isoformat()),
                    status=user.get('status', 'active'),
                    videoCount=video_count,
                    followerCount=follower_count,
                    totalViews=total_views,
                    totalLikes=total_likes,
                    lastActive=user.get('lastActive', datetime.utcnow().isoformat())
                ))

        return users
    except Exception as e:
        print(f"Error fetching admin users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.get("/videos", response_model=List[AdminVideo])
async def get_admin_videos(
    current_user_id: str = Depends(verify_admin),
    limit: int = 100,
    offset: int = 0
):
    """Get all videos for admin dashboard"""
    try:
        query = """
            SELECT * FROM video
            ORDER BY uploadedAt DESC
            LIMIT $limit
            START $offset
        """

        result = await db_client.query(query, {'limit': limit, 'offset': offset})

        videos = []
        if result and len(result) > 0 and 'result' in result[0]:
            for video in result[0]['result']:
                # Get creator info
                creator = await db_client.get_user_by_id(video.get('user_id', ''))
                creator_username = creator.get('username', '') if creator else ''

                # Get comment count
                comment_count_query = """
                    SELECT count() as count FROM comment
                    WHERE videoId = $video_id
                    GROUP ALL
                """
                comment_count_result = await db_client.query(comment_count_query, {'video_id': str(video.get('id', ''))})
                comment_count = 0
                if comment_count_result and len(comment_count_result) > 0 and 'result' in comment_count_result[0]:
                    res = comment_count_result[0]['result']
                    if res:
                        comment_count = res[0].get('count', 0)

                videos.append(AdminVideo(
                    id=str(video.get('id', '')),
                    title=video.get('title', ''),
                    creatorId=video.get('user_id', ''),
                    creatorUsername=creator_username,
                    uploadedAt=video.get('uploadedAt', datetime.utcnow().isoformat()),
                    status=video.get('status', 'active'),
                    views=video.get('views', 0),
                    likes=video.get('likes', 0),
                    comments=comment_count,
                    shares=video.get('shares', 0),
                    duration=video.get('duration', 0),
                    flagCount=video.get('flagCount', 0)
                ))

        return videos
    except Exception as e:
        print(f"Error fetching admin videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch videos")

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Suspend a user"""
    try:
        query = "UPDATE $user_id SET status = 'suspended'"
        await db_client.query(query, {'user_id': user_id})
        return {"success": True, "message": "User suspended"}
    except Exception as e:
        print(f"Error suspending user: {e}")
        raise HTTPException(status_code=500, detail="Failed to suspend user")

@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Ban a user"""
    try:
        query = "UPDATE $user_id SET status = 'banned'"
        await db_client.query(query, {'user_id': user_id})
        return {"success": True, "message": "User banned"}
    except Exception as e:
        print(f"Error banning user: {e}")
        raise HTTPException(status_code=500, detail="Failed to ban user")

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Activate a user"""
    try:
        query = "UPDATE $user_id SET status = 'active'"
        await db_client.query(query, {'user_id': user_id})
        return {"success": True, "message": "User activated"}
    except Exception as e:
        print(f"Error activating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate user")

@router.post("/videos/{video_id}/remove")
async def remove_video(
    video_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Remove a video"""
    try:
        query = "UPDATE $video_id SET status = 'removed'"
        await db_client.query(query, {'video_id': video_id})
        return {"success": True, "message": "Video removed"}
    except Exception as e:
        print(f"Error removing video: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove video")

@router.post("/videos/{video_id}/approve")
async def approve_video(
    video_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Approve a video"""
    try:
        query = "UPDATE $video_id SET status = 'active', flagCount = 0"
        await db_client.query(query, {'video_id': video_id})
        return {"success": True, "message": "Video approved"}
    except Exception as e:
        print(f"Error approving video: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve video")

@router.post("/videos/{video_id}/flag")
async def flag_video(
    video_id: str,
    current_user_id: str = Depends(verify_admin)
):
    """Flag a video"""
    try:
        query = "UPDATE $video_id SET status = 'flagged', flagCount = flagCount + 1"
        await db_client.query(query, {'video_id': video_id})
        return {"success": True, "message": "Video flagged"}
    except Exception as e:
        print(f"Error flagging video: {e}")
        raise HTTPException(status_code=500, detail="Failed to flag video")
