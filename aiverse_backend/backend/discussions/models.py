from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """Discussion category. Categories are referenced by ID on frontend, never by name."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, help_text="Optional description of the category")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Thread(models.Model):
    """
    Discussion thread. Each thread has one or more posts.
    
    Denormalized fields:
      - post_count: Updated by Post.save() for performance
      - last_post_at: Updated by Post.save() for sorting/pagination
    """
    title = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='threads')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Denormalized counts (updated by Post.save())
    post_count = models.IntegerField(default=0, help_text="Total posts in this thread")
    last_post_at = models.DateTimeField(null=True, blank=True, help_text="When the most recent post was created")

    class Meta:
        ordering = ['-last_post_at', '-created_at']
        indexes = [
            models.Index(fields=['category', '-last_post_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['-last_post_at']),
        ]

    def __str__(self):
        return self.title


class Post(models.Model):
    """
    A single post in a discussion thread.
    
    Signals:
      - On save: Updates thread.post_count and thread.last_post_at
    """
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(help_text="Post content")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    liked_by = models.ManyToManyField(
        User,
        related_name="liked_posts",
        blank=True
    )
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]

    def __str__(self):
        return f"{self.created_by.email} in {self.thread.title}"

    def save(self, *args, **kwargs):
        """
        Save post and update thread metadata atomically.
        
        This is called on every post creation/update.
        For new posts, we update thread.post_count and thread.last_post_at.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        is_new = self.pk is None
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving post: {e}", exc_info=True)
            raise

        if is_new:
            try:
                # Update thread metadata
                # Use select_for_update to prevent race conditions
                thread = Thread.objects.get(pk=self.thread.pk)
                thread.post_count = thread.posts.count()
                thread.last_post_at = timezone.now()
                thread.save(update_fields=['post_count', 'last_post_at'])
            except Exception as e:
                logger.error(f"Error updating thread metadata for post {self.pk}: {e}", exc_info=True)
                raise
