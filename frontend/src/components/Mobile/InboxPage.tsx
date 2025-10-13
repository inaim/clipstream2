import { useState, useEffect } from 'react';
import { MessageSquare, Send, ArrowLeft, User } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';

interface Conversation {
  id: string;
  participant1_id: string;
  participant2_id: string;
  created_at: string;
  updated_at: string;
  other_user: {
    id: string;
    username: string;
    display_name: string;
    avatar_url: string | null;
  };
  last_message?: {
    content: string;
    created_at: string;
    sender_id: string;
  };
  unread_count: number;
}

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  read: boolean;
  created_at: string;
}

export function InboxPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user]);

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.id);
      markAsRead(selectedConversation.id);
    }
  }, [selectedConversation]);

  const loadConversations = async () => {
    if (!user) return;

    const { data: convos } = await supabase
      .from('conversations')
      .select('*')
      .or(`participant1_id.eq.${user.id},participant2_id.eq.${user.id}`)
      .order('updated_at', { ascending: false });

    if (convos) {
      const enrichedConvos = await Promise.all(
        convos.map(async (convo) => {
          const otherUserId = convo.participant1_id === user.id ? convo.participant2_id : convo.participant1_id;

          const { data: otherUser } = await supabase
            .from('profiles')
            .select('id, username, display_name, avatar_url')
            .eq('id', otherUserId)
            .single();

          const { data: lastMsg } = await supabase
            .from('messages')
            .select('content, created_at, sender_id')
            .eq('conversation_id', convo.id)
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();

          const { count: unreadCount } = await supabase
            .from('messages')
            .select('id', { count: 'exact', head: true })
            .eq('conversation_id', convo.id)
            .eq('read', false)
            .neq('sender_id', user.id);

          return {
            ...convo,
            other_user: otherUser!,
            last_message: lastMsg || undefined,
            unread_count: unreadCount || 0,
          };
        })
      );

      setConversations(enrichedConvos);
    }
    setLoading(false);
  };

  const loadMessages = async (conversationId: string) => {
    const { data } = await supabase
      .from('messages')
      .select('*')
      .eq('conversation_id', conversationId)
      .order('created_at', { ascending: true });

    if (data) {
      setMessages(data);
    }
  };

  const markAsRead = async (conversationId: string) => {
    if (!user) return;

    await supabase
      .from('messages')
      .update({ read: true })
      .eq('conversation_id', conversationId)
      .neq('sender_id', user.id)
      .eq('read', false);
  };

  const sendMessage = async () => {
    if (!user || !selectedConversation || !newMessage.trim()) return;

    const { error } = await supabase.from('messages').insert({
      conversation_id: selectedConversation.id,
      sender_id: user.id,
      content: newMessage.trim(),
    });

    if (!error) {
      await supabase
        .from('conversations')
        .update({ updated_at: new Date().toISOString() })
        .eq('id', selectedConversation.id);

      setNewMessage('');
      loadMessages(selectedConversation.id);
      loadConversations();
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-black">
        <div className="text-white">Loading messages...</div>
      </div>
    );
  }

  if (selectedConversation) {
    return (
      <div className="h-full bg-black text-white flex flex-col">
        <div className="sticky top-0 bg-black/95 backdrop-blur-sm z-10 px-4 py-3 flex items-center gap-3 border-b border-gray-800">
          <button
            onClick={() => setSelectedConversation(null)}
            className="p-2 hover:bg-gray-800 rounded-full transition active:scale-95"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center flex-shrink-0">
            {selectedConversation.other_user.avatar_url ? (
              <img
                src={selectedConversation.other_user.avatar_url}
                alt={selectedConversation.other_user.display_name}
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <User className="w-5 h-5 text-white" />
            )}
          </div>
          <div className="flex-1">
            <div className="font-semibold">{selectedConversation.other_user.display_name}</div>
            <div className="text-xs text-gray-400">@{selectedConversation.other_user.username}</div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.map((message) => {
            const isOwn = message.sender_id === user?.id;
            return (
              <div
                key={message.id}
                className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[75%] px-4 py-2 rounded-2xl ${
                    isOwn
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-br-sm'
                      : 'bg-gray-800 text-white rounded-bl-sm'
                  }`}
                >
                  <p className="text-sm break-words">{message.content}</p>
                  <p className={`text-xs mt-1 ${isOwn ? 'text-blue-100' : 'text-gray-400'}`}>
                    {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="sticky bottom-0 bg-black border-t border-gray-800 p-4">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type a message..."
              className="flex-1 bg-gray-800 text-white px-4 py-3 rounded-full outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={!newMessage.trim()}
              className="p-3 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition active:scale-95"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-black text-white overflow-y-auto pb-20">
      <div className="sticky top-0 bg-black/95 backdrop-blur-sm z-10 px-4 py-4 border-b border-gray-800">
        <h1 className="text-2xl font-bold">Messages</h1>
      </div>

      {conversations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 px-4">
          <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mb-4">
            <MessageSquare className="w-10 h-10 text-gray-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">No messages yet</h3>
          <p className="text-gray-400 text-center text-sm">
            Start a conversation by visiting someone's profile
          </p>
        </div>
      ) : (
        <div className="divide-y divide-gray-800">
          {conversations.map((convo) => (
            <button
              key={convo.id}
              onClick={() => setSelectedConversation(convo)}
              className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-900/50 transition active:bg-gray-800"
            >
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center flex-shrink-0 relative">
                {convo.other_user.avatar_url ? (
                  <img
                    src={convo.other_user.avatar_url}
                    alt={convo.other_user.display_name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <User className="w-7 h-7 text-white" />
                )}
                {convo.unread_count > 0 && (
                  <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold">
                    {convo.unread_count}
                  </div>
                )}
              </div>
              <div className="flex-1 text-left">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold">{convo.other_user.display_name}</span>
                  {convo.last_message && (
                    <span className="text-xs text-gray-400">
                      {new Date(convo.last_message.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                    </span>
                  )}
                </div>
                <p className={`text-sm truncate ${convo.unread_count > 0 ? 'text-white font-semibold' : 'text-gray-400'}`}>
                  {convo.last_message?.content || 'Start a conversation'}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
