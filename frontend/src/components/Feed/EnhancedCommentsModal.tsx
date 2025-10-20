// Extend Comment type locally to include likes_count for this component
type CommentWithLikes = Comment & { likes_count?: number };
import { useState, useEffect } from 'react';
import { X, Send, User, Heart, MessageCircle, MoreVertical, Trash2 } from 'lucide-react';
import { surreal } from '../../lib/surrealdb';
import { useAuth } from '../../contexts/AuthContext';
import type { Database } from '../../lib/database.types';

type Video = Database['public']['Tables']['videos']['Row'];
type Comment = Database['public']['Tables']['comments']['Row'] & {
  profiles: Database['public']['Tables']['profiles']['Row'];
  replies?: Comment[];
  isLiked?: boolean;
};

interface EnhancedCommentsModalProps {
  video: Video;
  onClose: () => void;
  asPanel?: boolean;
}

export function EnhancedCommentsModal({ video, onClose, asPanel }: EnhancedCommentsModalProps) {
  const { user } = useAuth();
  const [comments, setComments] = useState<CommentWithLikes[]>([]);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Load comments effect and logic
  useEffect(() => {
    loadComments();
  }, [video.id]);

  async function loadComments() {
    setLoading(true);
    const { data } = await surreal
      .from('comments')
      .select(`*, profiles (*)`)
      .eq('video_id', video.id)
      .is('parent_comment_id', null)
      .order('created_at', { ascending: false });

    if (data) {
      const commentsWithReplies = await Promise.all(
  data.map(async (comment: CommentWithLikes) => {
          const { data: replies } = await surreal
            .from('comments')
            .select(`*, profiles (*)`)
            .eq('parent_comment_id', comment.id)
            .order('created_at', { ascending: true });

          let isLiked = false;
          if (user) {
            const { data: reaction } = await surreal
              .from('comment_reactions')
              .select('id')
              .eq('comment_id', comment.id)
              .eq('user_id', user.id)
              .maybeSingle();
            isLiked = !!reaction;
          }

          return {
            ...comment,
            replies: replies as CommentWithLikes[] || [],
            isLiked,
            likes_count: comment.likes_count ?? 0,
          };
        })
      );
  setComments(commentsWithReplies as CommentWithLikes[]);
    }
    setLoading(false);
  }

  // Render
  if (asPanel) {
    // Desktop: slide-in panel from right
    return (
      <div className="fixed inset-0 z-50 flex justify-end pointer-events-none">
        <div className="bg-white shadow-2xl h-full w-[340px] max-w-[30vw] flex flex-col pointer-events-auto animate-slidein">
          <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">
              {video.comments_count || 0} Comments
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-blue"></div>
              </div>
            ) : comments.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No comments yet. Be the first to comment!</p>
              </div>
            ) : (
              comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onReply={(id) => setReplyingTo(id)}
                  onLike={handleLikeComment}
                  onDelete={handleDeleteComment}
                  currentUserId={user?.id || ''}
                  isReply={false}
                />
              ))
            )}
          </div>
          <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
            {replyingTo && (
              <div className="mb-2 flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
                <span className="text-sm text-gray-600">
                  Replying to comment...
                </span>
                <button
                  className="text-xs text-red-500 hover:underline"
                  onClick={() => setReplyingTo(null)}
                >
                  Cancel
                </button>
              </div>
            )}
            <form onSubmit={(e) => handleSubmit(e, replyingTo)} className="flex gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-cyber flex-shrink-0 flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-sky-blue focus:border-transparent"
              />
              <button
                type="submit"
                disabled={!newComment.trim() || submitting}
                className="px-6 py-2 bg-gradient-cyber text-white rounded-full font-semibold hover:opacity-90 disabled:opacity-50 transition"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
        {/* Overlay for click-outside-to-close */}
        <div className="fixed inset-0 bg-black/30" onClick={onClose} />
        <style>{`.animate-slidein{animation:slidein .3s cubic-bezier(.4,0,.2,1)}@keyframes slidein{from{transform:translateX(100%);}to{transform:translateX(0);}}`}</style>
      </div>
    );
  }
  // Mobile: modal
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-end md:items-center md:justify-center z-50">
      <div className="bg-white w-full md:max-w-2xl md:rounded-2xl rounded-t-3xl max-h-[85vh] flex flex-col">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between rounded-t-3xl md:rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900">
            {video.comments_count || 0} Comments
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-blue"></div>
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No comments yet. Be the first to comment!</p>
            </div>
          ) : (
            comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onReply={(id) => setReplyingTo(id)}
                onLike={handleLikeComment}
                onDelete={handleDeleteComment}
                currentUserId={user?.id || ''}
                isReply={false}
              />
            ))
          )}
        </div>
        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
          {replyingTo && (
            <div className="mb-2 flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
              <span className="text-sm text-gray-600">
                Replying to comment...
              </span>
              <button
                onClick={() => setReplyingTo(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <form onSubmit={(e) => handleSubmit(e, replyingTo)} className="flex gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-cyber flex-shrink-0 flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-sky-blue focus:border-transparent"
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-6 py-2 bg-gradient-cyber text-white rounded-full font-semibold hover:opacity-90 disabled:opacity-50 transition"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );

  const handleSubmit = async (e: React.FormEvent, parentId: string | null = null) => {
    e.preventDefault();
    if (!user || !newComment.trim() || submitting) return;

    setSubmitting(true);

    try {
      await surreal.from('comments').insert({
        video_id: video.id,
        user_id: user.id,
        content: newComment,
        parent_comment_id: parentId,
      });

      setNewComment('');
      setReplyingTo(null);
      await loadComments();
    } catch (error) {
      console.error('Failed to post comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleLikeComment = async (commentId: string) => {
    if (!user) return;

    const comment = comments.find(c => c.id === commentId);
    if (!comment) return;

    try {
      if (comment.isLiked) {
        await surreal
          .from('comment_reactions')
          .delete()
          .eq('comment_id', commentId)
          .eq('user_id', user.id);
      } else {
        await surreal
          .from('comment_reactions')
          .insert({
            comment_id: commentId,
            user_id: user.id,
            reaction_type: 'like',
          });
      }

      await loadComments();
    } catch (error) {
      console.error('Failed to like comment:', error);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!user) return;

    try {
      await surreal
        .from('comments')
        .delete()
        .eq('id', commentId)
        .eq('user_id', user.id);

      await loadComments();
    } catch (error) {
      console.error('Failed to delete comment:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-end md:items-center md:justify-center z-50">
      <div className="bg-white w-full md:max-w-2xl md:rounded-2xl rounded-t-3xl max-h-[85vh] flex flex-col">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between rounded-t-3xl md:rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900">
            {video.comments_count || 0} Comments
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-blue"></div>
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No comments yet. Be the first to comment!</p>
            </div>
          ) : (
            comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onReply={(id) => setReplyingTo(id)}
                onLike={handleLikeComment}
                onDelete={handleDeleteComment}
                currentUserId={user?.id}
              />
            ))
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
          {replyingTo && (
            <div className="mb-2 flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
              <span className="text-sm text-gray-600">
                Replying to comment...
              </span>
              <button
                onClick={() => setReplyingTo(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <form onSubmit={(e) => handleSubmit(e, replyingTo)} className="flex gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-cyber flex-shrink-0 flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-sky-blue focus:border-transparent"
            />
            <button
              type="submit"
              disabled={!newComment.trim() || submitting}
              className="px-6 py-2 bg-gradient-cyber text-white rounded-full font-semibold hover:opacity-90 disabled:opacity-50 transition"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

interface CommentItemProps {
  comment: Comment;
  onReply: (id: string) => void;
  onLike: (id: string) => void;
  onDelete: (id: string) => void;
  currentUserId?: string;
  isReply?: boolean;
}

function CommentItem({ comment, onReply, onLike, onDelete, currentUserId, isReply = false }: CommentItemProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className={`${isReply ? 'ml-12' : ''}`}>
      <div className="flex gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-cyber flex-shrink-0 flex items-center justify-center">
          {comment.profiles.avatar_url ? (
            <img
              src={comment.profiles.avatar_url}
              alt={comment.profiles.username}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <User className="w-5 h-5 text-white" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="bg-gray-50 rounded-2xl px-4 py-3">
            <div className="flex items-center justify-between mb-1">
              <div>
                <span className="font-semibold text-sm text-gray-900">
                  {comment.profiles.display_name}
                </span>
                <span className="text-xs text-gray-500 ml-2">
                  @{comment.profiles.username}
                </span>
              </div>
              {currentUserId === comment.user_id && (
                <div className="relative">
                  <button
                    onClick={() => setShowMenu(!showMenu)}
                    className="p-1 hover:bg-gray-200 rounded-full"
                  >
                    <MoreVertical className="w-4 h-4 text-gray-500" />
                  </button>
                  {showMenu && (
                    <div className="absolute right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                      <button
                        onClick={() => {
                          onDelete(comment.id);
                          setShowMenu(false);
                        }}
                        className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
            <p className="text-gray-800 text-sm break-words">{comment.content}</p>
          </div>

          <div className="flex items-center gap-4 mt-2 ml-2">
            <button
              onClick={() => onLike(comment.id)}
              className={`flex items-center gap-1 text-sm transition ${
                comment.isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              }`}
            >
              <Heart className={`w-4 h-4 ${comment.isLiked ? 'fill-current' : ''}`} />
              {typeof comment.likes_count === 'number' && comment.likes_count > 0 && <span>{comment.likes_count}</span>}
            </button>

            {!isReply && (
              <button
                onClick={() => onReply(comment.id)}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-sky-blue transition"
              >
                <MessageCircle className="w-4 h-4" />
                Reply
              </button>
            )}

            <span className="text-xs text-gray-400">
              {new Date(comment.created_at).toLocaleDateString()}
            </span>
          </div>

          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 space-y-3">
              {comment.replies.map((reply) => (
                <CommentItem
                  key={reply.id}
                  comment={reply}
                  onReply={onReply}
                  onLike={onLike}
                  onDelete={onDelete}
                  currentUserId={currentUserId}
                  isReply
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
