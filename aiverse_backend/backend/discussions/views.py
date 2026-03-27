from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging
from rest_framework.decorators import api_view, permission_classes
from .models import Category, Thread, Post
from .serializers import (
    CategorySerializer,
    ThreadSerializer,
    ThreadCreateSerializer,
    PostSerializer,
    PostCreateSerializer,
)
from utils.cache import (
    cache_bust,
    cache_get,
    cache_set,
    categories_cache_key,
    CacheTTL,
)

logger = logging.getLogger(__name__)


class CategoryListView(APIView):
    """
    List all discussion categories.
    
    Frontend calls this to populate the category dropdown before creating a thread.
    Returns category objects with id, name, description.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Get all categories."""
        def _load_categories():
            # Ensure the dropdown is never empty (first deploy safety) and
            # never missing categories due to partial migrations.
            fallback = [
                {"name": "General", "description": "General discussion topics."},
                {"name": "Problem Help", "description": "Ask for help debugging your code or understanding problems."},
                {"name": "Research", "description": "Discuss papers, experiments, and research ideas."},
                {"name": "Career", "description": "Career advice and learning paths for ML engineering."},
                {"name": "Projects", "description": "Showcase projects and get feedback."},
                {"name": "Course Q&A", "description": "Questions about courses, lessons, and quizzes."},
            ]

            # Use get_or_create to avoid duplicates if deploy races.
            for item in fallback:
                Category.objects.get_or_create(
                    name=item["name"],
                    defaults={"description": item["description"]},
                )

            categories = Category.objects.all().order_by('name')
            return CategorySerializer(categories, many=True).data

        key = categories_cache_key()
        cached = cache_get(key)
        # If a stale empty list is cached, force a reload so the dropdown
        # never yields invalid IDs.
        if isinstance(cached, list) and len(cached) > 0:
            return Response(cached, status=status.HTTP_200_OK)

        data = _load_categories()
        cache_set(key, data, ttl=CacheTTL.CATEGORIES)
        return Response(data, status=status.HTTP_200_OK)


class ThreadListView(APIView):
    """
    List all discussion threads.
    
    Returns threads ordered by last_post_at (most recent first), with denormalized counts.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all threads."""
        threads = Thread.objects.all().select_related('category', 'created_by')
        serializer = ThreadSerializer(threads, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ThreadCreateView(APIView):
    """
    Create a new discussion thread with its first post (atomic).
    
    Frontend sends:
    {
      "title": "string",
      "category": 123,        // INTEGER ID, not name
      "content": "string"     // First post content
    }
    
    Backend returns:
      201: Created thread with serialized data
      400: ValidationError from serializer (invalid category, empty fields, etc.)
      401: Unauthenticated
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create thread and first post atomically."""
        serializer = ThreadCreateSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid thread creation data from user {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Create thread
                try:
                    thread = Thread.objects.create(
                        title=serializer.validated_data['title'],
                        category_id=serializer.validated_data['category'],
                        created_by=request.user
                    )
                    logger.info(f"Created thread {thread.id} by user {request.user.id}")
                except Exception as e:
                    logger.error(f"Failed to create thread object: {e}", exc_info=True)
                    raise

                # Create first post
                try:
                    post = Post.objects.create(
                        thread=thread,
                        content=serializer.validated_data['content'],
                        created_by=request.user
                    )
                    logger.info(f"Created first post {post.id} for thread {thread.id}")
                except Exception as e:
                    logger.error(f"Failed to create post object: {e}", exc_info=True)
                    raise

                # New content impacts category summaries/listing.
                try:
                    cache_bust(categories_cache_key())
                except Exception as e:
                    logger.warning(f"Failed to bust cache: {e}")
                    # Don't fail the request if cache bust fails

            return Response(
                ThreadSerializer(thread, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating thread: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to create thread', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ThreadDetailView(APIView):
    """Get a specific discussion thread."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get a single thread."""
        thread = get_object_or_404(Thread, pk=pk)
        serializer = ThreadSerializer(thread, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostListView(APIView):
    """
    List posts in a thread (paginated).
    
    Query params:
      - page: page number (default 1)
      - page_size: items per page (default 50)
    
    Returns:
      200: { posts: [...], total: count, page: int, page_size: int }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        """Get paginated posts for a thread."""
        thread = get_object_or_404(Thread, pk=thread_id)

        # Simple pagination
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, int(request.query_params.get('page_size', 50)))  # Cap at 100

        posts = thread.posts.order_by('created_at')
        total_count = posts.count()

        # Slice
        start = (page - 1) * page_size
        end = start + page_size
        paginated_posts = posts[start:end]

        serializer = PostSerializer(
            paginated_posts,
            many=True,
            context={'request': request}
        )

        return Response({
            'posts': serializer.data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
        }, status=status.HTTP_200_OK)
    


class PostCreateView(APIView):
    """
    Create a post in a thread.
    
    Frontend sends:
    { "content": "string" }
    
    Backend:
      - Creates post
      - Updates thread.post_count and thread.last_post_at
      - Returns serialized post
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        """Create a post in a thread."""
        thread = get_object_or_404(Thread, pk=thread_id)

        serializer = PostCreateSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid post creation data from user {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.create(
                thread=thread,
                content=serializer.validated_data['content'],
                created_by=request.user,
            )
            logger.info(f"Created post {post.id} in thread {thread_id} by user {request.user.id}")

            return Response(
                PostSerializer(post, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return Response(
                {'error': 'Failed to create post'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_post_like(request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if request.user in post.liked_by.all():
            post.liked_by.remove(request.user)
            liked = False
        else:
            post.liked_by.add(request.user)
            liked = True

        return Response(
        {
            "liked": liked,
            "likes_count": post.liked_by.count(),
        },
        status=status.HTTP_200_OK,
        )
