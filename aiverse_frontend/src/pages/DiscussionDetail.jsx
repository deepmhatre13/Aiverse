import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Clock, User, MessageSquare, Send, ThumbsUp } from 'lucide-react';
import api from '../api/axios';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

export default function DiscussionDetail() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [replyContent, setReplyContent] = useState('');

  const { data: thread, isLoading: threadLoading, error: threadError } = useQuery({
    queryKey: ['discussion', id],
    queryFn: async () => {
      try {
        const response = await api.get(`/api/discussions/threads/${id}/`);
        return response.data;
      } catch (err) {
        // Handle 401/403 gracefully
        if (err.response?.status === 401 || err.response?.status === 403) {
          return null; // Return null to show empty state
        }
        throw err; // Re-throw other errors
      }
    },
    retry: false,
  });

  const { data: messages, isLoading: messagesLoading, error: messagesError, refetch } = useQuery({
    queryKey: ['discussion-messages', id],
    queryFn: async () => {
      try {
        const response = await api.get(`/api/discussions/threads/${id}/messages/`);
        // Handle both array and paginated responses
        return response.data.posts || [];
      } catch (err) {
        // Handle 401/403 gracefully - return empty array
        if (err.response?.status === 401 || err.response?.status === 403) {
          return [];
        }
        throw err; // Re-throw other errors
      }
    },
    retry: false,
  });

  const replyMutation = useMutation({
    mutationFn: async (content) => {
      const response = await api.post(`/api/discussions/threads/${id}/messages/create/`, { content });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['discussion-messages', id]);
      setReplyContent('');
      toast.success('Reply posted');
    },
    onError: (err) => {
      // Handle 401/403 with friendly message
      if (err.response?.status === 401 || err.response?.status === 403) {
        toast.error('Login required to post replies');
      } else {
        const errorMessage = err.response?.data?.message || err.response?.data?.detail || 'Failed to post reply';
        toast.error(errorMessage);
      }
    },
  });

  const handleSubmitReply = (e) => {
    e.preventDefault();
    if (!replyContent.trim()) {
      toast.error('Please enter a reply');
      return;
    }
    replyMutation.mutate(replyContent);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  const likeMutation = useMutation({
  mutationFn: (postId) =>
    api.post(`/api/discussions/posts/${postId}/like/`),
  onSuccess: () => {
    queryClient.invalidateQueries(['discussion-messages', id]);
  },
});


  const isLoading = threadLoading || messagesLoading;
  const error = threadError || messagesError;

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <ErrorState message="Failed to load discussion" onRetry={refetch} />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Back Button */}
        <Link
          to="/discussions"
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Discussions
        </Link>

        {/* Thread Header */}
        <div className="glass rounded-xl p-6 mb-6">
          <h1 className="heading-secondary text-foreground mb-4">{thread?.title}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
            <span className="flex items-center gap-1">
              <User className="w-4 h-4" />
              {thread?.author?.name || 'Anonymous'}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatDate(thread?.created_at)}
            </span>
            <span className="px-2 py-1 bg-secondary rounded-md text-xs">
              {thread?.category}
            </span>
          </div>
          <div className="prose prose-neutral dark:prose-invert max-w-none">
            <p className="text-foreground whitespace-pre-wrap">{thread?.content}</p>
          </div>
        </div>

        {/* Replies */}
        <div className="mb-6">
          <h2 className="heading-tertiary text-foreground mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Replies ({messages?.length || 0})
          </h2>

          {messages?.length ? (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div key={message.id} className="card-elevated p-5">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-medium text-foreground">
                          {message.author?.name || 'Anonymous'}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatDate(message.created_at)}
                        </span>
                      </div>
                      <p className="text-foreground/90 whitespace-pre-wrap">{message.content}</p>
                      <div className="flex items-center gap-4 mt-3">
                        <button
  onClick={() => likeMutation.mutate(message.id)}
  className={`flex items-center gap-1 text-sm ${
    message.is_liked ? "text-primary" : "text-muted-foreground"
  }`}
>
  <ThumbsUp className="w-4 h-4" />
  {message.likes}
</button>

                        
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card-elevated p-8 text-center">
              <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No replies yet. Be the first to respond!</p>
            </div>
          )}
        </div>

        {/* Reply Form */}
        {isAuthenticated ? (
          <div className="glass rounded-xl p-6">
            <h3 className="font-serif text-lg font-medium mb-4">Post a Reply</h3>
            <form onSubmit={handleSubmitReply}>
              <Textarea
                placeholder="Share your thoughts..."
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                rows={4}
                className="bg-background resize-none mb-4"
              />
              <div className="flex justify-end">
                <Button
                  type="submit"
                  className="btn-wine gap-2"
                  disabled={replyMutation.isPending}
                >
                  <Send className="w-4 h-4" />
                  {replyMutation.isPending ? 'Posting...' : 'Post Reply'}
                </Button>
              </div>
            </form>
          </div>
        ) : (
          <div className="glass rounded-xl p-6 text-center">
            <p className="text-muted-foreground mb-4">
              Sign in to join the discussion
            </p>
            <Link to="/login">
              <Button className="btn-wine">Sign In</Button>
            </Link>
          </div>
        )}
      </div>
    </Layout>
  );
}
