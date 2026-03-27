"""
Production-grade Course System Models for ML Engineering Academy.

Supports:
- Free courses (YouTube-based)
- Paid courses (hosted video or secured CDN)
- Stripe payments (one-time + subscription-ready)
- Enrollment gating
- Course progression tracking
- Certificate generation
- Track integration
- Rating-based unlock logic
- Analytics tracking
- Instructor-ready extensibility
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import uuid

User = get_user_model()


class Course(models.Model):
    """
    Production-grade Course model for ML Engineering Academy.
    
    Supports:
    - Free courses (YouTube-based)
    - Paid courses (hosted video or secured CDN)
    - Track integration
    - Rating-based unlock logic
    - Analytics tracking
    """
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    # Core fields (Auto-incrementing ID inherited from Model)
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief 1-2 sentence summary for cards")
    thumbnail = models.URLField(max_length=500, blank=True, help_text="Course cover image URL")
    
    # Classification
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner', db_index=True)
    estimated_duration_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=0,
        help_text="Estimated total duration in hours"
    )
    
    # Track and rating integration
    track = models.ForeignKey(
        'tracks.Track',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text="Optional track this course belongs to"
    )
    required_rating = models.IntegerField(
        null=True, blank=True, default=None,
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        help_text="Minimum user rating required to enroll (null = no requirement)"
    )
    
    # Pricing
    is_free = models.BooleanField(default=True, db_index=True, help_text="True if course is free")
    is_paid = models.BooleanField(default=False, db_index=True, help_text="True if course requires payment")
    price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Price in currency units (null for free courses)"
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Denormalized stats (updated via signals/tasks)
    total_lessons = models.IntegerField(default=0, help_text="Cached lesson count")
    total_duration_minutes = models.IntegerField(default=0, help_text="Cached total duration")
    rating_average = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Average course rating (0-5)"
    )
    rating_count = models.IntegerField(default=0, help_text="Number of ratings")
    students_count = models.IntegerField(default=0, help_text="Number of enrolled students")
    completion_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentage of students who completed"
    )
    
    # Instructor (future extensibility)
    instructor_name = models.CharField(max_length=255, blank=True, help_text="Primary instructor name")
    instructor_bio = models.TextField(blank=True, help_text="Brief instructor bio")
    instructor_avatar = models.URLField(max_length=500, blank=True)
    
    # Pre-requisites and requirements
    prerequisites = models.JSONField(
        default=list, blank=True,
        help_text="List of prerequisite knowledge/skills"
    )
    what_youll_learn = models.JSONField(
        default=list, blank=True,
        help_text="Learning outcomes"
    )
    target_audience = models.JSONField(
        default=list, blank=True,
        help_text="Who this course is for"
    )
    
    # SEO and discoverability
    tags = models.JSONField(default=list, blank=True, help_text="Course tags for search")
    
    # Publishing
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['is_free', 'level']),
            models.Index(fields=['track', 'level']),
            models.Index(fields=['required_rating']),
            models.Index(fields=['-students_count']),
            models.Index(fields=['-rating_average']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Ensure is_free and is_paid are consistent
        if self.is_free:
            self.is_paid = False
        elif self.is_paid:
            self.is_free = False
        super().save(*args, **kwargs)
    
    def update_stats(self):
        """Update cached statistics. Call after lessons/enrollments change."""
        from django.db.models import Sum, Count
        
        lesson_stats = self.lessons.aggregate(
            count=Count('id'),
            total_duration=Sum('duration_minutes')
        )
        self.total_lessons = lesson_stats['count'] or 0
        self.total_duration_minutes = lesson_stats['total_duration'] or 0
        self.estimated_duration_hours = round(self.total_duration_minutes / 60, 1) if self.total_duration_minutes else 0
        
        # Update enrollment count
        self.students_count = self.enrollments.filter(status='active').count()
        
        # Update rating
        rating_stats = self.ratings.aggregate(
            avg=Avg('rating'),
            count=Count('id')
        )
        self.rating_average = rating_stats['avg'] or 0
        self.rating_count = rating_stats['count'] or 0
        
        # Update completion rate
        total_enrolled = self.students_count
        if total_enrolled > 0:
            completed = self.enrollments.filter(
                status='active',
                completion_percentage=100
            ).count()
            self.completion_rate = (completed / total_enrolled) * 100
        
        self.save(update_fields=[
            'total_lessons', 'total_duration_minutes', 'estimated_duration_hours',
            'students_count', 'rating_average', 'rating_count', 'completion_rate'
        ])
    
    @property
    def preview_lessons_count(self):
        return self.lessons.filter(is_preview=True).count()
    
    def user_meets_rating_requirement(self, user):
        """Check if user meets the required rating for this course."""
        if not self.required_rating:
            return True
        if not user.is_authenticated:
            return False
        return user.rating >= self.required_rating


class Lesson(models.Model):
    """
    Individual lesson within a course.
    
    Supports:
    - YouTube videos (free courses)
    - Hosted/CDN videos (paid courses with signed URLs)
    - Resources (PDFs, notebooks)
    - Preview lessons
    """
    
    VIDEO_TYPE_CHOICES = [
        ('youtube', 'YouTube'),
        ('hosted', 'Hosted/CDN Video'),
    ]
    
    # Core fields (Auto-incrementing ID inherited from Model)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Ordering
    order = models.PositiveIntegerField(default=0, db_index=True)
    
    # Video content
    video_type = models.CharField(
        max_length=20,
        choices=VIDEO_TYPE_CHOICES,
        default='youtube',
        help_text="Video source type"
    )
    youtube_url = models.URLField(
        max_length=500, blank=True,
        help_text="YouTube video URL (for free courses)"
    )
    youtube_id = models.CharField(
        max_length=32, blank=True,
        help_text="YouTube video ID extracted from URL"
    )
    hosted_video_url = models.URLField(
        max_length=500, blank=True,
        help_text="Hosted video URL (S3/CDN - DO NOT expose directly)"
    )
    hosted_video_key = models.CharField(
        max_length=255, blank=True,
        help_text="S3 object key for signed URL generation"
    )
    
    # Duration
    duration_minutes = models.PositiveIntegerField(default=0)
    
    # Access control
    is_preview = models.BooleanField(
        default=False, db_index=True,
        help_text="Preview lessons accessible without enrollment"
    )
    
    # Resources
    resources = models.JSONField(
        default=list, blank=True,
        help_text="List of resources [{name, url, type}]"
    )
    
    # Lesson notes/content
    notes = models.TextField(blank=True, help_text="Markdown lesson notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_lessons'
        ordering = ['course', 'order']
        unique_together = [['course', 'slug']]
        indexes = [
            models.Index(fields=['course', 'order']),
            models.Index(fields=['is_preview']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.order}. {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Extract YouTube ID from URL if provided
        if self.youtube_url and not self.youtube_id:
            self.youtube_id = self._extract_youtube_id(self.youtube_url)
        super().save(*args, **kwargs)
    
    def _extract_youtube_id(self, url):
        """Extract video ID from various YouTube URL formats."""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'  # Just the ID
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ''
    
    @property
    def youtube_embed_url(self):
        """Generate YouTube embed URL with restricted controls."""
        if self.video_type == 'youtube' and self.youtube_id:
            return f"https://www.youtube.com/embed/{self.youtube_id}?rel=0&modestbranding=1"
        return None

    def get_embed_url(self):
        """Return embed URL for free (YouTube) or None for hosted. Used by frontend."""
        if self.video_type == 'youtube' and self.youtube_id:
            return f"https://www.youtube.com/embed/{self.youtube_id}?rel=0&modestbranding=1"
        return None
    
    def get_signed_video_url(self, expiry_seconds=3600):
        """
        Generate signed URL for hosted videos.
        Called only after access verification.
        """
        if self.video_type != 'hosted' or not self.hosted_video_key:
            return None
        
        from django.conf import settings
        import boto3
        from botocore.config import Config
        from botocore.exceptions import NoCredentialsError
        
        try:
            # Use CloudFront signed URLs if configured, otherwise S3 presigned
            if hasattr(settings, 'CLOUDFRONT_DOMAIN') and settings.CLOUDFRONT_DOMAIN:
                # CloudFront signed URL logic
                return f"https://{settings.CLOUDFRONT_DOMAIN}/{self.hosted_video_key}"
            
            # S3 presigned URL
            if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
                    config=Config(signature_version='s3v4')
                )
                return s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': settings.VIDEO_BUCKET,
                        'Key': self.hosted_video_key
                    },
                    ExpiresIn=expiry_seconds
                )
        except (NoCredentialsError, AttributeError):
            pass
        
        # Fallback for development
        return self.hosted_video_url


class Enrollment(models.Model):
    """
    User enrollment in a course.
    
    Created via:
    - Direct enrollment (free courses)
    - Stripe payment webhook (paid courses)
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Auto-incrementing ID inherited from Model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Payment tracking
    is_paid = models.BooleanField(default=False, help_text="True if payment was made")
    payment_reference = models.CharField(
        max_length=255, blank=True, db_index=True,
        help_text="Stripe payment intent ID or other reference"
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Progress tracking
    completion_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    lessons_completed = models.IntegerField(default=0)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'learn_enrollments'
        unique_together = [['user', 'course']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['payment_reference']),
            models.Index(fields=['-last_accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.status})"
    
    def is_active(self):
        return self.status == 'active'
    
    def has_access(self):
        """Check if user has access to paid content."""
        if self.course.is_free:
            return True
        return self.status == 'active'
    
    def recalculate_progress(self):
        """Recalculate completion percentage from lesson progress."""
        total_lessons = self.course.total_lessons
        if total_lessons == 0:
            self.completion_percentage = 0
            self.lessons_completed = 0
        else:
            completed = LessonProgress.objects.filter(
                user=self.user,
                lesson__course=self.course,
                is_completed=True
            ).count()
            self.lessons_completed = completed
            self.completion_percentage = (completed / total_lessons) * 100
        
        self.save(update_fields=['completion_percentage', 'lessons_completed'])
        return self.completion_percentage


class LessonProgress(models.Model):
    """
    Track user progress through individual lessons.
    
    Records:
    - Completion status
    - Watch time for analytics
    - Video position for resume
    """
    
    # Auto-incrementing ID inherited from Model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name='progress_records',
        null=True, blank=True  # Null for free course access without formal enrollment
    )
    
    # Progress tracking
    is_completed = models.BooleanField(default=False, db_index=True)
    watch_time_seconds = models.PositiveIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)
    
    # Analytics
    first_watched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_watched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_lesson_progress'
        unique_together = [['user', 'lesson']]
        ordering = ['-last_watched_at']
        indexes = [
            models.Index(fields=['user', 'lesson']),
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_completed else f"{self.watch_time_seconds}s"
        return f"{self.user.email} - {self.lesson.title} ({status})"


class Certificate(models.Model):
    """
    Course completion certificate.
    
    Generated via Celery task when completion_percentage = 100%.
    Includes QR code for verification.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate_id = models.CharField(
        max_length=32, unique=True, db_index=True,
        help_text="Short unique ID for verification (e.g., CERT-XXXX-XXXX)"
    )
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name='certificate'
    )
    
    # Certificate data (snapshot at time of issue)
    user_name = models.CharField(max_length=255, help_text="User's name at time of issue")
    course_title = models.CharField(max_length=255, help_text="Course title at time of issue")
    course_level = models.CharField(max_length=20)
    completion_date = models.DateField()
    
    # PDF storage
    pdf_url = models.URLField(max_length=500, blank=True)
    pdf_file = models.FileField(upload_to='certificates/%Y/%m/', blank=True)
    
    # Verification
    verification_url = models.URLField(max_length=500, blank=True)
    qr_code_url = models.URLField(max_length=500, blank=True)
    
    # Metadata
    issued_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'learn_certificates'
        unique_together = [['user', 'course']]
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['user', '-issued_at']),
        ]
    
    def __str__(self):
        return f"{self.certificate_id} - {self.user_name} - {self.course_title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = self._generate_certificate_id()
        super().save(*args, **kwargs)
    
    def _generate_certificate_id(self):
        """Generate unique certificate ID."""
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        while True:
            cert_id = f"CERT-{''.join(random.choices(chars, k=4))}-{''.join(random.choices(chars, k=4))}"
            if not Certificate.objects.filter(certificate_id=cert_id).exists():
                return cert_id


class CourseRating(models.Model):
    """
    User rating and review for a course.
    Only enrolled users can rate.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_ratings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name='rating'
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_course_ratings'
        unique_together = [['user', 'course']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update course rating average
        self.course.update_stats()


class Payment(models.Model):
    """
    Payment records for course purchases.
    
    Stripe integration:
    - PaymentIntent for one-time purchases
    - Subscription support (future)
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    
    # Stripe data
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, db_index=True)
    stripe_client_secret = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    failure_reason = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'learn_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['stripe_checkout_session_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.status} - ${self.amount}"


# -----------------------------------------------------------------
# Analytics Models (for admin dashboard and insights)
# -----------------------------------------------------------------

class CourseAnalytics(models.Model):
    """
    Daily analytics snapshot for a course.
    Aggregated by Celery task.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(db_index=True)
    
    # Metrics
    views = models.IntegerField(default=0)
    enrollments = models.IntegerField(default=0)
    completions = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Engagement
    average_watch_time_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lesson_completions = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'learn_course_analytics'
        unique_together = [['course', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['course', '-date']),
        ]


class LessonAnalytics(models.Model):
    """
    Analytics for individual lessons.
    Used to identify drop-off points.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(db_index=True)
    
    # Metrics
    views = models.IntegerField(default=0)
    completions = models.IntegerField(default=0)
    average_watch_time_seconds = models.IntegerField(default=0)
    drop_off_count = models.IntegerField(default=0, help_text="Users who stopped at this lesson")
    
    class Meta:
        db_table = 'learn_lesson_analytics'
        unique_together = [['lesson', 'date']]
        ordering = ['-date']


# -----------------------------------------------------------------
# Quiz & MCQ Models (AI-Generated Assessments)
# -----------------------------------------------------------------

class Quiz(models.Model):
    """
    Quiz associated with a lesson.
    
    MCQs are auto-generated via Gemini after lesson creation.
    Quizzes are required for lesson completion (>= 70% to pass).
    """
    
    GENERATION_SOURCE_CHOICES = [
        ('gemini', 'Generated by Gemini'),
        ('manual', 'Manually Created'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quiz',
        help_text="Each lesson has exactly one quiz"
    )
    
    # Metadata
    title = models.CharField(max_length=255, blank=True, help_text="Quiz title (auto-generated)")
    description = models.TextField(blank=True, help_text="Quiz description")
    
    # Configuration
    total_questions = models.PositiveIntegerField(default=5)
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text="Minimum percentage to pass (0-100)"
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Time limit in seconds (null = no limit)"
    )
    
    # Generation tracking
    generated_by = models.CharField(
        max_length=20,
        choices=GENERATION_SOURCE_CHOICES,
        default='gemini'
    )
    generation_prompt = models.TextField(
        blank=True,
        help_text="Prompt used for Gemini generation"
    )
    source_transcript = models.TextField(
        blank=True,
        help_text="Lesson transcript used for generation"
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_quizzes'
        ordering = ['lesson__course', 'lesson__order']
    
    def __str__(self):
        return f"Quiz: {self.lesson.title}"
    
    @property
    def question_count(self):
        return self.questions.count()


class MCQ(models.Model):
    """
    Multiple Choice Question within a Quiz.
    
    Generated via Gemini with 4 options and explanation.
    """
    
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    # Question content
    question = models.TextField(help_text="The question text")
    order = models.PositiveIntegerField(default=0, db_index=True)
    
    # Options
    option_a = models.TextField(help_text="Option A text")
    option_b = models.TextField(help_text="Option B text")
    option_c = models.TextField(help_text="Option C text")
    option_d = models.TextField(help_text="Option D text")
    
    # Answer
    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        help_text="Correct answer (A/B/C/D)"
    )
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after answering"
    )
    
    # Metadata
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    topic = models.CharField(max_length=100, blank=True, help_text="Topic tag")
    
    # Stats (denormalized)
    times_answered = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'learn_mcqs'
        ordering = ['quiz', 'order']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]
    
    def __str__(self):
        return f"Q{self.order}: {self.question[:50]}..."
    
    @property
    def correct_rate(self):
        if self.times_answered == 0:
            return 0
        return (self.times_correct / self.times_answered) * 100


class QuizAttempt(models.Model):
    """
    User's attempt at a quiz.
    
    Records:
    - Answers given
    - Score achieved
    - Pass/fail status
    - Time taken
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        null=True, blank=True
    )
    
    # Attempt data
    answers = models.JSONField(
        default=dict,
        help_text="User answers: {question_id: 'A'|'B'|'C'|'D'}"
    )
    
    # Results
    score = models.PositiveIntegerField(
        default=0,
        help_text="Score as percentage (0-100)"
    )
    correct_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False, db_index=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'learn_quiz_attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['quiz', 'passed']),
            models.Index(fields=['user', '-started_at']),
        ]
    
    def __str__(self):
        status = "✓ Passed" if self.passed else "✗ Failed"
        return f"{self.user.email} - {self.quiz.lesson.title} ({status})"
    
    def calculate_score(self):
        """Calculate score from answers."""
        questions = self.quiz.questions.all()
        self.total_questions = questions.count()
        self.correct_count = 0
        
        for question in questions:
            user_answer = self.answers.get(str(question.id))
            if user_answer and user_answer.upper() == question.correct_option:
                self.correct_count += 1
                # Update MCQ stats
                question.times_correct += 1
            question.times_answered += 1
            question.save(update_fields=['times_answered', 'times_correct'])
        
        if self.total_questions > 0:
            self.score = int((self.correct_count / self.total_questions) * 100)
        else:
            self.score = 0
        
        self.passed = self.score >= self.quiz.passing_score
        self.completed_at = timezone.now()
        
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.time_taken_seconds = int(delta.total_seconds())
        
        self.save()


# -----------------------------------------------------------------
# Course Final Quiz Models (Post-Course Assessment)
# -----------------------------------------------------------------

class CourseQuiz(models.Model):
    """
    Final quiz for course completion assessment.
    
    Generated from all course lesson content via Gemini.
    Requires >= 75% to pass and unlock certificate.
    """
    
    GENERATION_SOURCE_CHOICES = [
        ('gemini', 'Generated by Gemini'),
        ('manual', 'Manually Created'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='final_quiz',
        help_text="Each course has one final quiz"
    )
    
    # Metadata
    title = models.CharField(max_length=255, blank=True, help_text="Quiz title (auto-generated)")
    description = models.TextField(blank=True, help_text="Quiz description")
    
    # Configuration
    total_questions = models.PositiveIntegerField(default=10)
    passing_score = models.PositiveIntegerField(
        default=75,
        help_text="Minimum percentage to pass (0-100)"
    )
    time_limit_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Time limit in seconds (null = no limit)"
    )
    
    # Generation tracking
    generated_by = models.CharField(
        max_length=20,
        choices=GENERATION_SOURCE_CHOICES,
        default='gemini'
    )
    generation_prompt = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learn_course_quizzes'
        ordering = ['course__title']
    
    def __str__(self):
        return f"Final Quiz: {self.course.title}"
    
    @property
    def question_count(self):
        return self.questions.count()


class CourseMCQ(models.Model):
    """
    Multiple Choice Question for final course quiz.
    """
    
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_quiz = models.ForeignKey(CourseQuiz, on_delete=models.CASCADE, related_name='questions')
    
    # Question content
    question = models.TextField(help_text="The question text")
    order = models.PositiveIntegerField(default=0, db_index=True)
    
    # Options
    option_a = models.TextField(help_text="Option A text")
    option_b = models.TextField(help_text="Option B text")
    option_c = models.TextField(help_text="Option C text")
    option_d = models.TextField(help_text="Option D text")
    
    # Answer
    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        help_text="Correct answer (A/B/C/D)"
    )
    explanation = models.TextField(blank=True)
    
    # Metadata
    source_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='course_mcqs',
        help_text="Lesson this question is derived from"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    topic = models.CharField(max_length=100, blank=True)
    
    # Stats
    times_answered = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'learn_course_mcqs'
        ordering = ['course_quiz', 'order']
        indexes = [
            models.Index(fields=['course_quiz', 'order']),
        ]
    
    def __str__(self):
        return f"Q{self.order}: {self.question[:50]}..."
    
    @property
    def correct_rate(self):
        if self.times_answered == 0:
            return 0
        return (self.times_correct / self.times_answered) * 100


class CourseQuizAttempt(models.Model):
    """
    User's attempt at a final course quiz.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_quiz_attempts')
    course_quiz = models.ForeignKey(CourseQuiz, on_delete=models.CASCADE, related_name='attempts')
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='course_quiz_attempts',
        null=True, blank=True
    )
    
    # Attempt data
    answers = models.JSONField(default=dict)
    
    # Results
    score = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False, db_index=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'learn_course_quiz_attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'course_quiz']),
            models.Index(fields=['course_quiz', 'passed']),
        ]
    
    def __str__(self):
        status = "✓ Passed" if self.passed else "✗ Failed"
        return f"{self.user.email} - {self.course_quiz.course.title} Final ({status})"
    
    def calculate_score(self):
        """Calculate score from answers."""
        questions = self.course_quiz.questions.all()
        self.total_questions = questions.count()
        self.correct_count = 0
        
        for question in questions:
            user_answer = self.answers.get(str(question.id))
            if user_answer and user_answer.upper() == question.correct_option:
                self.correct_count += 1
                question.times_correct += 1
            question.times_answered += 1
            question.save(update_fields=['times_answered', 'times_correct'])
        
        if self.total_questions > 0:
            self.score = int((self.correct_count / self.total_questions) * 100)
        else:
            self.score = 0
        
        self.passed = self.score >= self.course_quiz.passing_score
        self.completed_at = timezone.now()
        
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.time_taken_seconds = int(delta.total_seconds())
        
        self.save()
        
        # If passed, trigger certificate generation
        if self.passed and self.enrollment and not self.enrollment.certificate_issued:
            from .tasks import generate_certificate_task
            generate_certificate_task.delay(str(self.enrollment.id))
