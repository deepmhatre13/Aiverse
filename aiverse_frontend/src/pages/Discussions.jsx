import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MessageSquare, Plus, Clock, User, ArrowRight } from 'lucide-react';
import api from '../api/axios';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

export default function Discussions() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newThread, setNewThread] = useState({ title: '', content: '', category: '' });
  const [validationErrors, setValidationErrors] = useState({});

  // Safety fallback: UI must never show an empty category error.
  // Backend seeds categories if the DB is empty, but we keep these as a last resort.
  const FALLBACK_CATEGORIES = [
    { id: 1, name: 'General' },
    { id: 2, name: 'Problem Help' },
    { id: 3, name: 'Research' },
    { id: 4, name: 'Career' },
    { id: 5, name: 'Projects' },
    { id: 6, name: 'Course Q&A' },
  ];

  /**
   * Fetch all discussion threads.
   * Categories must be fetched separately for the dropdown.
   */
  const { data: threads = [], isLoading, error, refetch } = useQuery({
    queryKey: ['discussions-threads'],
    queryFn: async () => {
      const response = await api.get('/api/discussions/threads/');
      return response.data || [];
    },
    retry: 1,
  });

  /**
   * Fetch all categories.
   * Frontend displays these as options, using category.id as the value.
   * NEVER hardcode category names on frontend.
   */
  const { data: categoriesData = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['discussion-categories'],
    queryFn: async () => {
      const response = await api.get('/api/discussions/categories/');
      return response.data || [];
    },
    retry: 1,
  });

  /**
   * Create a new thread with first post (atomic backend operation).
   * 
   * Frontend sends:
   * { title, category: INTEGER_ID, content }
   * 
   * Backend returns:
   * - 201: Thread created successfully
   * - 400: Validation errors (category invalid, empty fields, etc.)
   * - 401: Unauthenticated
   */
  const createThreadMutation = useMutation({
    mutationFn: async (data) => {
      const response = await api.post('/api/discussions/threads/create/', {
        title: data.title.trim(),
        category: parseInt(data.category, 10),  // CRITICAL: Send as integer, not string
        content: data.content.trim(),
      });
      return response.data;
    },
    onSuccess: () => {
      // Refetch threads list to show new thread
      queryClient.invalidateQueries({ queryKey: ['discussions-threads'] });
      setIsCreateOpen(false);
      setNewThread({ title: '', content: '', category: '' });
      setValidationErrors({});
      toast.success('Thread created successfully!');
    },
    onError: (err) => {
      if (err.response?.status === 401) {
        toast.error('Login required to create a thread');
      } else if (err.response?.status === 400 && err.response?.data) {
        // Parse backend validation errors (e.g., { "category": ["Invalid category ID..."] })
        const errors = err.response.data;
        if (typeof errors === 'object') {
          setValidationErrors(errors);
          // Also show the first error as a toast for visibility
          const firstError = Object.values(errors)[0];
          if (Array.isArray(firstError)) {
            toast.error(firstError[0]);
          } else {
            toast.error(firstError);
          }
        } else {
          toast.error('Validation failed. Please check your input.');
        }
      } else {
        const errorMsg = err.response?.data?.detail || 'Failed to create thread';
        toast.error(errorMsg);
      }
    },
  });

  const handleCreateThread = (e) => {
    e.preventDefault();
    setValidationErrors({});

    // Client-side validation (for UX before sending to backend)
    if (!newThread.title.trim()) {
      setValidationErrors({ title: 'Title is required' });
      return;
    }
    if (!newThread.content.trim()) {
      setValidationErrors({ content: 'Content is required' });
      return;
    }
    if (!newThread.category) {
      setValidationErrors({ category: 'Please select a category' });
      return;
    }

    createThreadMutation.mutate(newThread);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="heading-primary text-foreground mb-2">Discussions</h1>
            <p className="text-muted-foreground">
              Connect with the community, ask questions, and share knowledge
            </p>
          </div>

          {/* Create Thread Dialog */}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="btn-wine gap-2">
                <Plus className="w-4 h-4" />
                New Thread
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-serif text-xl">Create New Thread</DialogTitle>
                <DialogDescription>
                  Start a new discussion thread by providing a title, category, and your question or topic.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateThread} className="space-y-4 mt-4">
                <div>
                  <label className="label-text mb-2 block">Title *</label>
                  <Input
                    placeholder="What's your question or topic?"
                    value={newThread.title}
                    onChange={(e) => {
                      setNewThread({ ...newThread, title: e.target.value });
                      if (validationErrors.title) {
                        setValidationErrors({ ...validationErrors, title: '' });
                      }
                    }}
                    className={`bg-background ${validationErrors.title ? 'border-red-500' : ''}`}
                  />
                  {validationErrors.title && (
                    <p className="text-xs text-red-500 mt-1">
                      {validationErrors.title}
                    </p>
                  )}
                </div>

                <div>
                  <label className="label-text mb-2 block">Category *</label>
                  <Select
                    value={newThread.category}
                    onValueChange={(value) => {
                      setNewThread({ ...newThread, category: value });
                      if (validationErrors.category) {
                        setValidationErrors({ ...validationErrors, category: '' });
                      }
                    }}
                  >
                    <SelectTrigger className={`bg-background ${validationErrors.category ? 'border-red-500' : ''}`}>
                      <SelectValue placeholder="Select a category..." />
                    </SelectTrigger>
                    <SelectContent>
                      {categoriesLoading ? (
                        <div className="p-2 text-sm text-muted-foreground">Loading categories...</div>
                      ) : (
                        (categoriesData.length > 0 ? categoriesData : FALLBACK_CATEGORIES).map((cat) => (
                          <SelectItem key={cat.id} value={String(cat.id)}>
                            {cat.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  {validationErrors.category && (
                    <p className="text-xs text-red-500 mt-1">
                      {validationErrors.category}
                    </p>
                  )}
                </div>

                <div>
                  <label className="label-text mb-2 block">Content *</label>
                  <Textarea
                    placeholder="Describe your question or share your thoughts..."
                    value={newThread.content}
                    onChange={(e) => {
                      setNewThread({ ...newThread, content: e.target.value });
                      if (validationErrors.content) {
                        setValidationErrors({ ...validationErrors, content: '' });
                      }
                    }}
                    rows={6}
                    className={`bg-background resize-none ${validationErrors.content ? 'border-red-500' : ''}`}
                  />
                  {validationErrors.content && (
                    <p className="text-xs text-red-500 mt-1">
                      {validationErrors.content}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">Markdown is supported</p>
                </div>

                <div className="flex justify-end gap-3">
                  <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="btn-wine"
                    disabled={createThreadMutation.isPending}
                  >
                    {createThreadMutation.isPending ? 'Creating...' : 'Create Thread'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Thread List */}
        {error && error.response?.status !== 401 && error.response?.status !== 403 ? (
          <ErrorState message="Failed to load discussions" onRetry={refetch} />
        ) : !threads || threads.length === 0 ? (
          <EmptyState
            icon={MessageSquare}
            title="No discussions yet"
            description="Be the first to start a conversation"
            action={
              <Button onClick={() => setIsCreateOpen(true)} className="btn-wine gap-2">
                <Plus className="w-4 h-4" />
                Create Thread
              </Button>
            }
          />
        ) : (
          <div className="space-y-4">
            {threads.map((thread) => (
              <Link
                key={thread.id}
                to={`/discussions/${thread.id}`}
                className="block card-elevated p-6 group hover:border-primary/30 transition-all"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-serif text-lg font-medium text-foreground group-hover:text-primary transition-colors line-clamp-1">
                          {thread.title}
                        </h3>
                      </div>
                      <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
                    </div>
                    <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-muted-foreground">
                      <span className="px-2 py-1 bg-secondary rounded-md">
                        {thread.category_name || 'General'}
                      </span>
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {thread.created_by_name || 'Anonymous'}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(thread.last_post_at || thread.created_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        {thread.post_count || 0} {thread.post_count === 1 ? 'post' : 'posts'}
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
