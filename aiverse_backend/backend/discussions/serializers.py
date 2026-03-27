from rest_framework import serializers
from .models import Category, Thread, Post


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for discussion categories."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for discussion posts."""
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, allow_blank=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    is_author = serializers.SerializerMethodField()
    author=serializers.CharField(source="created_by.email",read_only=True)
    likes = serializers.IntegerField(source="liked_by.count", read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id',
            'thread',
            'created_by_id',
            'created_by_name',
            'created_by_email',
            'content',
            'created_at',
            'is_author',
            'author',
            'likes',
            'is_liked',
        ]
        read_only_fields = [
            'id',
            'thread',
            'created_by_id',
            'created_by_name',
            'created_by_email',
            'created_at',
        ]

    def get_is_author(self, obj):
        """Check if the current user is the post author."""
        try:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                return obj.created_by == request.user
        except (AttributeError, TypeError, KeyError):
            pass
        return False

    def get_is_liked(self, obj):
        try:
            user = self.context.get("request").user
            return user.is_authenticated and obj.liked_by.filter(id=user.id).exists()
        except (AttributeError, TypeError, KeyError):
            return False

class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for discussion threads with denormalized counts and nested posts."""
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True)
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, allow_blank=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    latest_posts = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = [
            'id',
            'title',
            'category_id',
            'category_name',
            'created_by_id',
            'created_by_name',
            'created_by_email',
            'created_at',
            'post_count',
            'last_post_at',
            'latest_posts',
        ]
        read_only_fields = [
            'id',
            'category_id',
            'category_name',
            'created_by_id',
            'created_by_name',
            'created_by_email',
            'created_at',
            'post_count',
            'last_post_at',
        ]

    def get_latest_posts(self, obj):
        """Return last 3 posts (most recent first)."""
        try:
            latest = obj.posts.order_by('-created_at')[:3]
            return PostSerializer(latest, many=True, context=self.context).data
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting latest posts for thread {obj.id}: {e}", exc_info=True)
            return []


class ThreadCreateSerializer(serializers.Serializer):
    """
    Input serializer for creating a discussion thread with first post.
    
    CRITICAL: Frontend MUST send category as an ID (integer), NOT a name.
    """
    title = serializers.CharField(max_length=255, min_length=1)
    category = serializers.IntegerField(help_text="Category ID (integer), not name")
    content = serializers.CharField(min_length=1, help_text="First post content")

    def validate_title(self, value):
        """Ensure title is non-empty after stripping."""
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError('Title cannot be empty')
        if len(stripped) > 255:
            raise serializers.ValidationError('Title must be 255 characters or less')
        return stripped

    def validate_content(self, value):
        """Ensure content is non-empty after stripping."""
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError('Content cannot be empty')
        return stripped

    def validate_category(self, value):
        """
        Validate that category ID exists in the database.
        
        Raises:
            serializers.ValidationError: If category doesn't exist
        """
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError(
                f'Invalid category ID: {value}. Please check available categories.'
            )
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                'Category must be a valid integer ID'
            )
        return value


class PostCreateSerializer(serializers.Serializer):
    """Input serializer for creating a post in a thread."""
    content = serializers.CharField(min_length=1)

    def validate_content(self, value):
        """Ensure content is non-empty after stripping."""
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError('Content cannot be empty')
        return stripped
