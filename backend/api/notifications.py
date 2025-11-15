from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
from db.surrealdb_client import db_client
from utils.auth import get_current_user
import asyncio
import json

router = APIRouter()

class Notification(BaseModel):
    id: str
    type: Literal['like', 'comment', 'follow', 'mention', 'video', 'gift', 'system']
    userId: Optional[str] = None
    username: Optional[str] = None
    displayName: Optional[str] = None
    avatar: Optional[str] = None
    content: str
    videoId: Optional[str] = None
    videoThumbnail: Optional[str] = None
    timestamp: str
    read: bool

class NotificationCreate(BaseModel):
    type: Literal['like', 'comment', 'follow', 'mention', 'video', 'gift', 'system']
    userId: str
    content: str
    videoId: Optional[str] = None
    targetUserId: str  # The user who should receive the notification

@router.get("", response_model=List[Notification])
async def get_notifications(
    current_user_id: str = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get all notifications for the current user"""
    try:
        # Query notifications from database
        query = """
            SELECT * FROM notification
            WHERE targetUserId = $user_id
            ORDER BY timestamp DESC
            LIMIT $limit
            START $offset
        """

        result = await db_client.query(query, {
            'user_id': current_user_id,
            'limit': limit,
            'offset': offset
        })

        notifications = []
        if result and len(result) > 0 and 'result' in result[0]:
            for notif in result[0]['result']:
                # Get user details if userId is present
                user_data = {}
                if notif.get('userId'):
                    user = await db_client.get_user_by_id(notif['userId'])
                    if user:
                        user_data = {
                            'username': user.get('username'),
                            'displayName': user.get('display_name'),
                            'avatar': user.get('avatar')
                        }

                notifications.append(Notification(
                    id=str(notif.get('id', '')),
                    type=notif.get('type', 'system'),
                    userId=notif.get('userId'),
                    username=user_data.get('username'),
                    displayName=user_data.get('displayName'),
                    avatar=user_data.get('avatar'),
                    content=notif.get('content', ''),
                    videoId=notif.get('videoId'),
                    videoThumbnail=notif.get('videoThumbnail'),
                    timestamp=notif.get('timestamp', datetime.utcnow().isoformat()),
                    read=notif.get('read', False)
                ))

        return notifications
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")

@router.post("", status_code=201)
async def create_notification(
    notification: NotificationCreate,
    current_user_id: str = Depends(get_current_user)
):
    """Create a new notification"""
    try:
        # Create notification in database
        query = """
            CREATE notification CONTENT {
                type: $type,
                userId: $user_id,
                content: $content,
                videoId: $video_id,
                targetUserId: $target_user_id,
                timestamp: time::now(),
                read: false
            }
        """

        result = await db_client.query(query, {
            'type': notification.type,
            'user_id': notification.userId,
            'content': notification.content,
            'video_id': notification.videoId,
            'target_user_id': notification.targetUserId
        })

        return {"success": True, "message": "Notification created"}
    except Exception as e:
        print(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        query = """
            UPDATE $notif_id SET read = true
            WHERE targetUserId = $user_id
        """

        await db_client.query(query, {
            'notif_id': notification_id,
            'user_id': current_user_id
        })

        return {"success": True, "message": "Notification marked as read"}
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user_id: str = Depends(get_current_user)
):
    """Mark all notifications as read for the current user"""
    try:
        query = """
            UPDATE notification SET read = true
            WHERE targetUserId = $user_id
        """

        await db_client.query(query, {'user_id': current_user_id})

        return {"success": True, "message": "All notifications marked as read"}
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        query = """
            DELETE $notif_id
            WHERE targetUserId = $user_id
        """

        await db_client.query(query, {
            'notif_id': notification_id,
            'user_id': current_user_id
        })

        return {"success": True, "message": "Notification deleted"}
    except Exception as e:
        print(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

@router.get("/stream")
async def notification_stream(
    request: Request,
    current_user_id: str = Depends(get_current_user)
):
    """Server-Sent Events stream for real-time notifications"""
    async def event_generator():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Query for new notifications
                query = """
                    SELECT * FROM notification
                    WHERE targetUserId = $user_id AND read = false
                    ORDER BY timestamp DESC
                    LIMIT 10
                """

                result = await db_client.query(query, {'user_id': current_user_id})

                if result and len(result) > 0 and 'result' in result[0]:
                    for notif in result[0]['result']:
                        # Get user details
                        user_data = {}
                        if notif.get('userId'):
                            user = await db_client.get_user_by_id(notif['userId'])
                            if user:
                                user_data = {
                                    'username': user.get('username'),
                                    'displayName': user.get('display_name'),
                                    'avatar': user.get('avatar')
                                }

                        notification_data = {
                            'id': str(notif.get('id', '')),
                            'type': notif.get('type', 'system'),
                            'userId': notif.get('userId'),
                            'username': user_data.get('username'),
                            'displayName': user_data.get('displayName'),
                            'avatar': user_data.get('avatar'),
                            'content': notif.get('content', ''),
                            'videoId': notif.get('videoId'),
                            'videoThumbnail': notif.get('videoThumbnail'),
                            'timestamp': notif.get('timestamp', datetime.utcnow().isoformat()),
                            'read': notif.get('read', False)
                        }

                        yield f"data: {json.dumps(notification_data)}\n\n"

                # Wait before next check (every 5 seconds)
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in notification stream: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
