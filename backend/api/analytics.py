from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime, timedelta
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class VideoStats(BaseModel):
    id: str
    title: str
    thumbnail: Optional[str] = None
    status: str
    uploadedAt: str
    duration: int
    views: int
    likes: int
    comments: int
    shares: int
    watchTime: int
    engagementRate: float
    revenue: Optional[float] = None

class AnalyticsData(BaseModel):
    totalViews: int
    totalLikes: int
    totalComments: int
    totalShares: int
    totalRevenue: float
    avgEngagementRate: float
    followerGrowth: int
    topVideo: Optional[VideoStats] = None

@router.get("", response_model=AnalyticsData)
async def get_analytics(
    current_user_id: str = Depends(get_current_user),
    range: Literal['7d', '30d', '90d', 'all'] = '30d'
):
    """Get analytics data for the current user"""
    try:
        # Calculate date filter
        date_filter = ""
        if range != 'all':
            days = int(range.replace('d', ''))
            date_filter = f"AND uploadedAt > time::now() - {days}d"

        # Get total views
        views_query = f"""
            SELECT sum(views) as total FROM video
            WHERE user_id = $user_id {date_filter}
            GROUP ALL
        """
        views_result = await db_client.query(views_query, {'user_id': current_user_id})
        total_views = 0
        if views_result and len(views_result) > 0 and 'result' in views_result[0]:
            res = views_result[0]['result']
            if res:
                total_views = res[0].get('total', 0)

        # Get total likes
        likes_query = f"""
            SELECT count() as count FROM like
            INNER JOIN video ON like.videoId = video.id
            WHERE video.user_id = $user_id {date_filter}
            GROUP ALL
        """
        likes_result = await db_client.query(likes_query, {'user_id': current_user_id})
        total_likes = 0
        if likes_result and len(likes_result) > 0 and 'result' in likes_result[0]:
            res = likes_result[0]['result']
            if res:
                total_likes = res[0].get('count', 0)

        # Get total comments
        comments_query = f"""
            SELECT count() as count FROM comment
            INNER JOIN video ON comment.videoId = video.id
            WHERE video.user_id = $user_id {date_filter}
            GROUP ALL
        """
        comments_result = await db_client.query(comments_query, {'user_id': current_user_id})
        total_comments = 0
        if comments_result and len(comments_result) > 0 and 'result' in comments_result[0]:
            res = comments_result[0]['result']
            if res:
                total_comments = res[0].get('count', 0)

        # Get total shares
        shares_query = f"""
            SELECT sum(shares) as total FROM video
            WHERE user_id = $user_id {date_filter}
            GROUP ALL
        """
        shares_result = await db_client.query(shares_query, {'user_id': current_user_id})
        total_shares = 0
        if shares_result and len(shares_result) > 0 and 'result' in shares_result[0]:
            res = shares_result[0]['result']
            if res:
                total_shares = res[0].get('total', 0)

        # Get follower growth
        follower_growth = 0  # Placeholder - implement based on your follower tracking

        # Calculate average engagement rate
        avg_engagement_rate = 0.0
        if total_views > 0:
            total_engagement = total_likes + total_comments + total_shares
            avg_engagement_rate = (total_engagement / total_views) * 100

        # Get top performing video
        top_video_query = f"""
            SELECT * FROM video
            WHERE user_id = $user_id {date_filter}
            ORDER BY views DESC
            LIMIT 1
        """
        top_video_result = await db_client.query(top_video_query, {'user_id': current_user_id})
        top_video = None

        if top_video_result and len(top_video_result) > 0 and 'result' in top_video_result[0]:
            videos = top_video_result[0]['result']
            if videos:
                video = videos[0]
                # Get video stats
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

                views = video.get('views', 0)
                likes = video.get('likes', 0)
                shares = video.get('shares', 0)
                engagement_rate = 0.0
                if views > 0:
                    engagement_rate = ((likes + comment_count + shares) / views) * 100

                top_video = VideoStats(
                    id=str(video.get('id', '')),
                    title=video.get('title', ''),
                    thumbnail=video.get('thumbnail_url'),
                    status=video.get('status', ''),
                    uploadedAt=video.get('uploadedAt', ''),
                    duration=video.get('duration', 0),
                    views=views,
                    likes=likes,
                    comments=comment_count,
                    shares=shares,
                    watchTime=0,  # Placeholder
                    engagementRate=engagement_rate,
                    revenue=0.0  # Placeholder
                )

        return AnalyticsData(
            totalViews=total_views,
            totalLikes=total_likes,
            totalComments=total_comments,
            totalShares=total_shares,
            totalRevenue=0.0,  # Placeholder
            avgEngagementRate=avg_engagement_rate,
            followerGrowth=follower_growth,
            topVideo=top_video
        )
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@router.get("/videos", response_model=List[VideoStats])
async def get_user_video_stats(
    current_user_id: str = Depends(get_current_user)
):
    """Get detailed stats for all user's videos"""
    try:
        query = """
            SELECT * FROM video
            WHERE user_id = $user_id
            ORDER BY uploadedAt DESC
        """

        result = await db_client.query(query, {'user_id': current_user_id})

        videos = []
        if result and len(result) > 0 and 'result' in result[0]:
            for video in result[0]['result']:
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

                views = video.get('views', 0)
                likes = video.get('likes', 0)
                shares = video.get('shares', 0)
                engagement_rate = 0.0
                if views > 0:
                    engagement_rate = ((likes + comment_count + shares) / views) * 100

                videos.append(VideoStats(
                    id=str(video.get('id', '')),
                    title=video.get('title', ''),
                    thumbnail=video.get('thumbnail_url'),
                    status=video.get('status', ''),
                    uploadedAt=video.get('uploadedAt', ''),
                    duration=video.get('duration', 0),
                    views=views,
                    likes=likes,
                    comments=comment_count,
                    shares=shares,
                    watchTime=0,  # Placeholder
                    engagementRate=engagement_rate,
                    revenue=0.0  # Placeholder
                ))

        return videos
    except Exception as e:
        print(f"Error fetching video stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch video stats")
