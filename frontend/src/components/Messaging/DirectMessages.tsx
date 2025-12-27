import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Search,
  MoreVertical,
  Image,
  Video,
  Smile,
  Heart,
  ArrowLeft,
  Check,
  CheckCheck,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

interface Conversation {
  id: string;
  userId: string;
  username: string;
  displayName: string;
  avatar?: string;
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  isOnline: boolean;
}

interface Message {
  id: string;
  senderId: string;
  content: string;
  type: 'text' | 'image' | 'video' | 'like';
  timestamp: string;
  read: boolean;
}

export const DirectMessages: React.FC<{ onUnreadChange?: (n: number) => void }> = ({ onUnreadChange }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const res = await fetch('/api/v1/messages/conversations', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
        const unread = (data || []).reduce((acc: number, c: any) => acc + (c.unread_count || c.unreadCount || 0), 0);
        onUnreadChange?.(unread);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  };

  const fetchMessages = async (conversationId: string) => {
    try {
      const res = await fetch(`/api/v1/messages/conversations/${conversationId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        // Mark messages as read
        markAsRead(conversationId);
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const markAsRead = async (conversationId: string) => {
    try {
      await fetch(`/api/v1/messages/conversations/${conversationId}/read`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
      });
      // Update conversation unread count
      setConversations((prev) => {
        const updated = prev.map((conv) => (conv.id === conversationId ? { ...conv, unreadCount: 0 } : conv));
        const unread = updated.reduce((acc: number, c: any) => acc + (c.unread_count || c.unreadCount || c.unreadCount === 0 ? c.unread_count || c.unreadCount || 0 : 0), 0);
        onUnreadChange?.(unread);
        return updated;
      });
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;

    const tempMessage: Message = {
      id: Date.now().toString(),
      senderId: user?.id || '',
      content: newMessage,
      type: 'text',
      timestamp: new Date().toISOString(),
      read: false,
    };

    setMessages([...messages, tempMessage]);
    setNewMessage('');

    try {
      const res = await fetch('/api/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
        body: JSON.stringify({
          recipientId: selectedConversation.userId,
          content: newMessage,
          type: 'text',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        // Update the temporary message with the real one
        setMessages((msgs) => msgs.map((msg) => (msg.id === tempMessage.id ? data : msg)));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const sendLike = async () => {
    if (!selectedConversation) return;

    const likeMessage: Message = {
      id: Date.now().toString(),
      senderId: user?.id || '',
      content: '',
      type: 'like',
      timestamp: new Date().toISOString(),
      read: false,
    };

    setMessages([...messages, likeMessage]);

    try {
      await fetch('/api/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('clipstream_token')}`,
        },
        body: JSON.stringify({
          recipientId: selectedConversation.userId,
          type: 'like',
        }),
      });
    } catch (error) {
      console.error('Failed to send like:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatMessageTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 7 * 24) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const filteredConversations = conversations.filter(
    (conv) =>
      conv.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.displayName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Conversations List */}
      <div
        className={`w-full md:w-96 bg-white border-r border-gray-200 flex flex-col ${
          selectedConversation ? 'hidden md:flex' : 'flex'
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold mb-3">Messages</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Conversations */}
        <div className="flex-1 overflow-y-auto">
          {filteredConversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => setSelectedConversation(conversation)}
              className={`w-full p-4 flex items-start space-x-3 hover:bg-gray-50 transition ${
                selectedConversation?.id === conversation.id ? 'bg-blue-50' : ''
              }`}
            >
              <div className="relative flex-shrink-0">
                {conversation.avatar ? (
                  <img
                    src={conversation.avatar}
                    alt=""
                    className="w-12 h-12 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                    {conversation.displayName.charAt(0)}
                  </div>
                )}
                {conversation.isOnline && (
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                )}
              </div>
              <div className="flex-1 min-w-0 text-left">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-gray-900 truncate">
                    {conversation.displayName}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatMessageTime(conversation.lastMessageTime)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600 truncate">{conversation.lastMessage}</p>
                  {conversation.unreadCount > 0 && (
                    <span className="ml-2 bg-blue-600 text-white text-xs font-semibold rounded-full w-5 h-5 flex items-center justify-center">
                      {conversation.unreadCount}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      {selectedConversation ? (
        <div className="flex-1 flex flex-col bg-white">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setSelectedConversation(null)}
                className="md:hidden p-2 hover:bg-gray-100 rounded-full"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              {selectedConversation.avatar ? (
                <img
                  src={selectedConversation.avatar}
                  alt=""
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                  {selectedConversation.displayName.charAt(0)}
                </div>
              )}
              <div>
                <div className="font-semibold">{selectedConversation.displayName}</div>
                <div className="text-sm text-gray-500">
                  {selectedConversation.isOnline ? 'Active now' : 'Offline'}
                </div>
              </div>
            </div>
            <button className="p-2 hover:bg-gray-100 rounded-full">
              <MoreVertical className="w-5 h-5 text-gray-600" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => {
              const isMine = message.senderId === user?.id;
              return (
                <div key={message.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                  {message.type === 'like' ? (
                    <div className="flex items-center space-x-2">
                      <Heart className="w-12 h-12 text-red-500 fill-current animate-pulse" />
                    </div>
                  ) : (
                    <div
                      className={`max-w-xs md:max-w-md px-4 py-2 rounded-2xl ${
                        isMine
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="break-words">{message.content}</p>
                      <div
                        className={`flex items-center justify-end space-x-1 mt-1 text-xs ${
                          isMine ? 'text-blue-100' : 'text-gray-500'
                        }`}
                      >
                        <span>{formatMessageTime(message.timestamp)}</span>
                        {isMine && (
                          message.read ? (
                            <CheckCheck className="w-3 h-3" />
                          ) : (
                            <Check className="w-3 h-3" />
                          )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <button className="p-2 hover:bg-gray-100 rounded-full transition">
                <Image className="w-5 h-5 text-gray-600" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-full transition">
                <Smile className="w-5 h-5 text-gray-600" />
              </button>
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type a message..."
                className="flex-1 px-4 py-2 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {newMessage.trim() ? (
                <button
                  onClick={sendMessage}
                  className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition"
                >
                  <Send className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={sendLike}
                  className="p-2 hover:bg-gray-100 rounded-full transition"
                >
                  <Heart className="w-5 h-5 text-red-500" />
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="hidden md:flex flex-1 items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Your Messages</h3>
            <p className="text-gray-500">
              Send private photos and messages to a friend or group.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
