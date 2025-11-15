from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime
from db.surrealdb_client import db_client
from utils.auth import get_current_user

router = APIRouter()

class Message(BaseModel):
    id: str
    senderId: str
    content: str
    type: Literal['text', 'image', 'video', 'like']
    timestamp: str
    read: bool

class Conversation(BaseModel):
    id: str
    userId: str
    username: str
    displayName: str
    avatar: Optional[str] = None
    lastMessage: str
    lastMessageTime: str
    unreadCount: int
    isOnline: bool

class MessageCreate(BaseModel):
    recipientId: str
    content: Optional[str] = None
    type: Literal['text', 'image', 'video', 'like'] = 'text'

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(current_user_id: str = Depends(get_current_user)):
    """Get all conversations for the current user"""
    try:
        # Query to get all unique conversations
        query = """
            LET $conversations = (
                SELECT
                    senderId as userId,
                    recipientId as otherUserId
                FROM message
                WHERE senderId = $user_id OR recipientId = $user_id
            );

            LET $unique_users = array::distinct(
                array::concat(
                    array::distinct($conversations.*.userId),
                    array::distinct($conversations.*.otherUserId)
                )
            );

            SELECT * FROM $unique_users WHERE $parent != $user_id;
        """

        result = await db_client.query(query, {'user_id': current_user_id})

        conversations = []

        # For each unique user, get conversation details
        if result and len(result) > 0:
            for user_id in result[0].get('result', []):
                if user_id == current_user_id:
                    continue

                # Get user details
                user = await db_client.get_user_by_id(user_id)
                if not user:
                    continue

                # Get last message
                last_msg_query = """
                    SELECT * FROM message
                    WHERE (senderId = $user_id AND recipientId = $other_id)
                       OR (senderId = $other_id AND recipientId = $user_id)
                    ORDER BY timestamp DESC
                    LIMIT 1
                """

                last_msg_result = await db_client.query(last_msg_query, {
                    'user_id': current_user_id,
                    'other_id': user_id
                })

                last_message = "No messages yet"
                last_message_time = datetime.utcnow().isoformat()

                if last_msg_result and len(last_msg_result) > 0 and 'result' in last_msg_result[0]:
                    msgs = last_msg_result[0]['result']
                    if msgs:
                        last_msg = msgs[0]
                        if last_msg.get('type') == 'like':
                            last_message = "❤️"
                        else:
                            last_message = last_msg.get('content', '')
                        last_message_time = last_msg.get('timestamp', last_message_time)

                # Get unread count
                unread_query = """
                    SELECT count() as count FROM message
                    WHERE recipientId = $user_id
                      AND senderId = $other_id
                      AND read = false
                    GROUP ALL
                """

                unread_result = await db_client.query(unread_query, {
                    'user_id': current_user_id,
                    'other_id': user_id
                })

                unread_count = 0
                if unread_result and len(unread_result) > 0 and 'result' in unread_result[0]:
                    res = unread_result[0]['result']
                    if res:
                        unread_count = res[0].get('count', 0)

                conversations.append(Conversation(
                    id=f"conv_{current_user_id}_{user_id}",
                    userId=user_id,
                    username=user.get('username', ''),
                    displayName=user.get('display_name', ''),
                    avatar=user.get('avatar'),
                    lastMessage=last_message,
                    lastMessageTime=last_message_time,
                    unreadCount=unread_count,
                    isOnline=user.get('isOnline', False)
                ))

        # Sort by last message time
        conversations.sort(key=lambda x: x.lastMessageTime, reverse=True)

        return conversations
    except Exception as e:
        print(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")

@router.get("/conversations/{conversation_id}", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user),
    limit: int = 100
):
    """Get all messages in a conversation"""
    try:
        # Extract other user ID from conversation ID
        # Format: conv_{user1}_{user2}
        parts = conversation_id.split('_')
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="Invalid conversation ID")

        other_user_id = parts[2] if parts[1] == current_user_id else parts[1]

        query = """
            SELECT * FROM message
            WHERE (senderId = $user_id AND recipientId = $other_id)
               OR (senderId = $other_id AND recipientId = $user_id)
            ORDER BY timestamp ASC
            LIMIT $limit
        """

        result = await db_client.query(query, {
            'user_id': current_user_id,
            'other_id': other_user_id,
            'limit': limit
        })

        messages = []
        if result and len(result) > 0 and 'result' in result[0]:
            for msg in result[0]['result']:
                messages.append(Message(
                    id=str(msg.get('id', '')),
                    senderId=msg.get('senderId', ''),
                    content=msg.get('content', ''),
                    type=msg.get('type', 'text'),
                    timestamp=msg.get('timestamp', datetime.utcnow().isoformat()),
                    read=msg.get('read', False)
                ))

        return messages
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.post("", status_code=201)
async def send_message(
    message: MessageCreate,
    current_user_id: str = Depends(get_current_user)
):
    """Send a new message"""
    try:
        query = """
            CREATE message CONTENT {
                senderId: $sender_id,
                recipientId: $recipient_id,
                content: $content,
                type: $type,
                timestamp: time::now(),
                read: false
            }
        """

        result = await db_client.query(query, {
            'sender_id': current_user_id,
            'recipient_id': message.recipientId,
            'content': message.content or '',
            'type': message.type
        })

        if result and len(result) > 0 and 'result' in result[0]:
            msg = result[0]['result'][0]
            return Message(
                id=str(msg.get('id', '')),
                senderId=msg.get('senderId', ''),
                content=msg.get('content', ''),
                type=msg.get('type', 'text'),
                timestamp=msg.get('timestamp', datetime.utcnow().isoformat()),
                read=msg.get('read', False)
            )

        return {"success": True, "message": "Message sent"}
    except Exception as e:
        print(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """Mark all messages in a conversation as read"""
    try:
        # Extract other user ID
        parts = conversation_id.split('_')
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="Invalid conversation ID")

        other_user_id = parts[2] if parts[1] == current_user_id else parts[1]

        query = """
            UPDATE message SET read = true
            WHERE recipientId = $user_id AND senderId = $other_id
        """

        await db_client.query(query, {
            'user_id': current_user_id,
            'other_id': other_user_id
        })

        return {"success": True, "message": "Conversation marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking conversation as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark conversation as read")
