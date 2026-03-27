"""
Production-grade Serializers for ML Engineering Academy Course System.

Strict data contracts with:
- Consistent JSON structure
- Role-based video access
- Progress tracking
- Rating validation
- Certificate verification
"""

from rest_framework import serializers
from django.utils import timezone
from .models import (
    Course, Lesson, Enrollment, LessonProgress,
    Certificate, CourseRating, Payment,
    CourseAnalytics, LessonAnalytics, Quiz, MCQ, QuizAttempt
)


# -----------------------------------------------------------------
# Base/Utility Serializers
# -----------------------------------------------------------------

class TrackMiniSerializer(serializers.Serializer):
    """Minimal track info for course cards."""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    level = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)


# -----------------------------------------------------------------
# Lesson Serializers
# -----------------------------------------------------------------

class LessonListSerializer(serializers.ModelSerializer):
    """
    Lesson list serializer (curriculum view).
    NO video URLs - just metadata for curriculum display.
    """
    
    is_accessible = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'order',
            'video_type',
            'duration_minutes',
            'is_preview',
            'is_accessible',
            'is_unlocked',
            'progress',
        ]
    
    def get_is_accessible(self, obj):
        """
        Check if user can access this lesson.
        
        Access rules:
        1. Preview lessons: Always accessible
        2. Free courses: Always accessible for authenticated users
        3. Paid courses: Only with active enrollment
        """
        request = self.context.get('request')
        
        # Preview lessons always accessible
        if obj.is_preview:
            return True
        
        # Unauthenticated users can only see previews
        if not request or not request.user.is_authenticated:
            return False
        
        # Staff/admin always have access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Free courses always accessible when authenticated
        if obj.course.is_free:
            return True
        
        # Paid courses require active enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=obj.course,
            status='active'
        ).first()
        
        return enrollment is not None
    
    def get_is_unlocked(self, obj):
        """Unlocked = accessible AND (first lesson OR previous completed for paid)."""
        accessible = self.get_is_accessible(obj)
        if not accessible:
            return False
        if obj.course.is_free:
            return True
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        prev = Lesson.objects.filter(
            course=obj.course,
            order__lt=obj.order
        ).order_by('-order').first()
        if not prev:
            return True
        return LessonProgress.objects.filter(
            user=request.user,
            lesson=prev,
            is_completed=True
        ).exists()
    
    def get_progress(self, obj):
        """Get user progress for this lesson."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            progress = LessonProgress.objects.get(
                user=request.user,
                lesson=obj
            )
            return {
                'is_completed': progress.is_completed,
                'watch_time_seconds': progress.watch_time_seconds,
                'last_position_seconds': progress.last_position_seconds,
            }
        except LessonProgress.DoesNotExist:
            return None


class LessonDetailSerializer(serializers.ModelSerializer):
    """
    Full lesson detail with video URL (access-controlled).
    
    Video URL is only returned if user has access.
    For YouTube: returns embed_url (preferred) and video_url.
    For hosted videos: returns signed temporary URL.
    """
    
    video_url = serializers.SerializerMethodField()
    embed_url = serializers.SerializerMethodField()
    youtube_id = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    resources = serializers.JSONField(read_only=True)
    next_lesson = serializers.SerializerMethodField()
    prev_lesson = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'order',
            'video_type',
            'video_url',
            'embed_url',
            'youtube_id',
            'duration_minutes',
            'is_preview',
            'is_unlocked',
            'notes',
            'resources',
            'progress',
            'next_lesson',
            'prev_lesson',
            'created_at',
        ]
    
    def _has_access(self, obj):
        """Check if current user has access to video content."""
        request = self.context.get('request')
        if obj.is_preview:
            return True
        if not request or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        if obj.course.is_free:
            return True
        return Enrollment.objects.filter(
            user=request.user,
            course=obj.course,
            status='active'
        ).exists()
    
    def get_is_unlocked(self, obj):
        """Unlocked = accessible AND (first lesson OR previous completed for paid)."""
        if not self._has_access(obj):
            return False
        if obj.course.is_free:
            return True
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        prev = Lesson.objects.filter(
            course=obj.course,
            order__lt=obj.order
        ).order_by('-order').first()
        if not prev:
            return True
        return LessonProgress.objects.filter(
            user=request.user,
            lesson=prev,
            is_completed=True
        ).exists()
    
    def get_video_url(self, obj):
        """
        Return video URL only if user has access.
        For hosted: signed URL. For YouTube: embed URL (legacy).
        """
        if not self._has_access(obj):
            return None
        if obj.video_type == 'hosted':
            return obj.get_signed_video_url(expiry_seconds=3600)
        elif obj.video_type == 'youtube':
            return obj.get_embed_url() or getattr(obj, 'youtube_embed_url', None)
        return None
    
    def get_embed_url(self, obj):
        """
        Return YouTube embed URL for free courses.
        Format: https://www.youtube.com/embed/VIDEO_ID?rel=0&modestbranding=1
        """
        import logging
        logger = logging.getLogger(__name__)
        if not self._has_access(obj):
            return None
        if obj.video_type == 'youtube':
            url = getattr(obj, 'youtube_embed_url', None) or (obj.get_embed_url() if callable(getattr(obj, 'get_embed_url', None)) else None)
            if url:
                logger.debug("Lesson %s embed_url=%s", obj.id, url)
                return url
            if getattr(obj, 'youtube_id', None):
                url = f"https://www.youtube.com/embed/{obj.youtube_id}?rel=0&modestbranding=1"
                logger.debug("Lesson %s embed_url (from youtube_id)=%s", obj.id, url)
                return url
        return None
    
    def get_youtube_id(self, obj):
        """Return YouTube ID only if user has access."""
        if not self._has_access(obj):
            return None
        return obj.youtube_id if obj.video_type == 'youtube' else None
    
    def get_progress(self, obj):
        """Get user progress for this lesson."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            progress = LessonProgress.objects.get(
                user=request.user,
                lesson=obj
            )
            return {
                'is_completed': progress.is_completed,
                'watch_time_seconds': progress.watch_time_seconds,
                'last_position_seconds': progress.last_position_seconds,
                'completed_at': progress.completed_at,
            }
        except LessonProgress.DoesNotExist:
            return None
    
    def get_next_lesson(self, obj):
        """Get next lesson in course."""
        next_lesson = Lesson.objects.filter(
            course=obj.course,
            order__gt=obj.order
        ).order_by('order').first()
        
        if next_lesson:
            return {
                'id': str(next_lesson.id),
                'slug': next_lesson.slug,
                'title': next_lesson.title,
            }
        return None
    
    def get_prev_lesson(self, obj):
        """Get previous lesson in course."""
        prev_lesson = Lesson.objects.filter(
            course=obj.course,
            order__lt=obj.order
        ).order_by('-order').first()
        
        if prev_lesson:
            return {
                'id': str(prev_lesson.id),
                'slug': prev_lesson.slug,
                'title': prev_lesson.title,
            }
        return None


# -----------------------------------------------------------------
# Course Serializers
# -----------------------------------------------------------------

class CourseListSerializer(serializers.ModelSerializer):
    """
    Course card serializer for list views.
    
    Includes:
    - Basic course info
    - Enrollment status for current user
    - Rating lock status
    """
    
    is_enrolled = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    lock_reason = serializers.SerializerMethodField()
    track = TrackMiniSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'short_description',
            'thumbnail',
            'level',
            'estimated_duration_hours',
            'is_free',
            'is_paid',
            'price',
            'currency',
            'total_lessons',
            'total_duration_minutes',
            'rating_average',
            'rating_count',
            'students_count',
            'required_rating',
            'track',
            'is_enrolled',
            'is_locked',
            'lock_reason',
            'instructor_name',
            'tags',
            'created_at',
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return Enrollment.objects.filter(
            user=request.user,
            course=obj,
            status='active'
        ).exists()
    
    def get_is_locked(self, obj):
        """Check if course is locked due to rating requirement."""
        if not obj.required_rating:
            return False
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return True
        
        return request.user.rating < obj.required_rating
    
    def get_lock_reason(self, obj):
        """Get reason why course is locked."""
        if not self.get_is_locked(obj):
            return None
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return f"Requires {obj.required_rating} rating. Login to check your rating."
        
        return f"Requires {obj.required_rating} rating. Your rating: {request.user.rating}"


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Full course detail serializer.
    
    Includes:
    - All course info
    - Lessons list (with access status)
    - Enrollment and progress info
    - Rating requirement status
    """
    
    lessons = LessonListSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    lock_reason = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    track = TrackMiniSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'short_description',
            'thumbnail',
            'level',
            'estimated_duration_hours',
            'is_free',
            'is_paid',
            'price',
            'currency',
            'total_lessons',
            'total_duration_minutes',
            'rating_average',
            'rating_count',
            'students_count',
            'completion_rate',
            'required_rating',
            'track',
            'instructor_name',
            'instructor_bio',
            'instructor_avatar',
            'prerequisites',
            'what_youll_learn',
            'target_audience',
            'tags',
            'lessons',
            'is_enrolled',
            'is_locked',
            'lock_reason',
            'enrollment_status',
            'progress',
            'user_rating',
            'created_at',
            'updated_at',
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return Enrollment.objects.filter(
            user=request.user,
            course=obj,
            status='active'
        ).exists()
    
    def get_is_locked(self, obj):
        """Check if course is locked due to rating requirement."""
        if not obj.required_rating:
            return False
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return True
        
        return request.user.rating < obj.required_rating
    
    def get_lock_reason(self, obj):
        """Get reason why course is locked."""
        if not self.get_is_locked(obj):
            return None
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return f"Requires {obj.required_rating} rating. Login to check your rating."
        
        return f"Requires {obj.required_rating} rating. Your rating: {request.user.rating}"
    
    def get_enrollment_status(self, obj):
        """Get user's enrollment status for this course."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=obj
            )
            return {
                'status': enrollment.status,
                'has_access': enrollment.has_access(),
                'enrolled_at': enrollment.enrolled_at,
                'activated_at': enrollment.activated_at,
                'certificate_issued': enrollment.certificate_issued,
            }
        except Enrollment.DoesNotExist:
            return None
    
    def get_progress(self, obj):
        """Get user's progress in this course."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=obj,
                status='active'
            )
            
            # Get resume lesson (last accessed or first incomplete)
            last_progress = LessonProgress.objects.filter(
                user=request.user,
                lesson__course=obj,
                is_completed=False
            ).order_by('lesson__order').first()
            
            resume_lesson = None
            if last_progress:
                resume_lesson = {
                    'id': str(last_progress.lesson.id),
                    'slug': last_progress.lesson.slug,
                    'title': last_progress.lesson.title,
                    'order': last_progress.lesson.order,
                }
            
            # Calculate estimated time remaining
            completed_minutes = sum(
                lp.lesson.duration_minutes 
                for lp in LessonProgress.objects.filter(
                    user=request.user,
                    lesson__course=obj,
                    is_completed=True
                ).select_related('lesson')
            )
            remaining_minutes = obj.total_duration_minutes - completed_minutes
            
            return {
                'completion_percentage': float(enrollment.completion_percentage),
                'lessons_completed': enrollment.lessons_completed,
                'total_lessons': obj.total_lessons,
                'resume_lesson': resume_lesson,
                'remaining_minutes': max(0, remaining_minutes),
                'last_accessed_at': enrollment.last_accessed_at,
            }
        except Enrollment.DoesNotExist:
            return None
    
    def get_user_rating(self, obj):
        """Get user's rating for this course."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            rating = CourseRating.objects.get(
                user=request.user,
                course=obj
            )
            return {
                'rating': rating.rating,
                'review': rating.review,
                'created_at': rating.created_at,
            }
        except CourseRating.DoesNotExist:
            return None


# -----------------------------------------------------------------
# Enrollment Serializers
# -----------------------------------------------------------------

class EnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment with course details."""
    
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',
            'status',
            'is_paid',
            'completion_percentage',
            'lessons_completed',
            'certificate_issued',
            'enrolled_at',
            'activated_at',
            'last_accessed_at',
        ]


class EnrollmentProgressSerializer(serializers.ModelSerializer):
    """Enrollment progress for dashboard."""
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_thumbnail = serializers.URLField(source='course.thumbnail', read_only=True)
    total_lessons = serializers.IntegerField(source='course.total_lessons', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course_title',
            'course_slug',
            'course_thumbnail',
            'status',
            'completion_percentage',
            'lessons_completed',
            'total_lessons',
            'certificate_issued',
            'last_accessed_at',
        ]


# -----------------------------------------------------------------
# Progress Tracking Serializers
# -----------------------------------------------------------------

class ProgressUpdateSerializer(serializers.Serializer):
    """
    Input serializer for updating lesson progress.
    Accepts both 'completed' and 'is_completed' for frontend compatibility.
    """
    
    watch_time_seconds = serializers.IntegerField(min_value=0, required=False, default=0)
    last_position_seconds = serializers.IntegerField(min_value=0, required=False, default=0)
    is_completed = serializers.BooleanField(required=False, default=False)
    completed = serializers.BooleanField(required=False, default=False)
    
    def validate(self, attrs):
        is_done = attrs.get('is_completed', False) or attrs.get('completed', False)
        attrs['is_completed'] = is_done
        return attrs


class LessonCompleteSerializer(serializers.Serializer):
    """Input serializer for marking lesson complete."""
    
    watch_time_seconds = serializers.IntegerField(min_value=0, required=False, default=0)


# -----------------------------------------------------------------
# Certificate Serializers
# -----------------------------------------------------------------

class CertificateSerializer(serializers.ModelSerializer):
    """Certificate details."""
    
    class Meta:
        model = Certificate
        fields = [
            'id',
            'certificate_id',
            'user_name',
            'course_title',
            'course_level',
            'completion_date',
            'pdf_url',
            'verification_url',
            'qr_code_url',
            'issued_at',
        ]


class CertificateVerifySerializer(serializers.ModelSerializer):
    """Public certificate verification response."""
    
    class Meta:
        model = Certificate
        fields = [
            'certificate_id',
            'user_name',
            'course_title',
            'course_level',
            'completion_date',
            'issued_at',
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['valid'] = True
        return data


# -----------------------------------------------------------------
# Rating Serializers
# -----------------------------------------------------------------

class CourseRatingSerializer(serializers.ModelSerializer):
    """Course rating with user info."""
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseRating
        fields = [
            'id',
            'user_name',
            'rating',
            'review',
            'created_at',
            'updated_at',
        ]
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class CourseRatingCreateSerializer(serializers.Serializer):
    """Input serializer for creating/updating course rating."""
    
    rating = serializers.IntegerField(min_value=1, max_value=5, required=True)
    review = serializers.CharField(max_length=5000, required=False, allow_blank=True)


# -----------------------------------------------------------------
# Payment Serializers
# -----------------------------------------------------------------

class CreateCheckoutSessionSerializer(serializers.Serializer):
    """
    Input serializer for creating Stripe checkout session.
    
    Uses Checkout Session (recommended) instead of PaymentIntent
    for better UX and hosted checkout page.
    """
    
    course_slug = serializers.SlugField(required=True)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class PaymentIntentSerializer(serializers.Serializer):
    """
    Input serializer for creating Stripe PaymentIntent.
    
    For custom payment forms with Elements.
    """
    
    course_slug = serializers.SlugField(required=True)


class PaymentSerializer(serializers.ModelSerializer):
    """Payment record details."""
    
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'course_title',
            'amount',
            'currency',
            'status',
            'created_at',
            'succeeded_at',
        ]


# -----------------------------------------------------------------
# Analytics Serializers
# -----------------------------------------------------------------

class CourseAnalyticsSerializer(serializers.ModelSerializer):
    """Course analytics for admin dashboard."""
    
    class Meta:
        model = CourseAnalytics
        fields = [
            'date',
            'views',
            'enrollments',
            'completions',
            'revenue',
            'average_watch_time_minutes',
            'lesson_completions',
        ]


class LessonAnalyticsSerializer(serializers.ModelSerializer):
    """Lesson analytics for identifying drop-off."""
    
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_order = serializers.IntegerField(source='lesson.order', read_only=True)
    
    class Meta:
        model = LessonAnalytics
        fields = [
            'date',
            'lesson_title',
            'lesson_order',
            'views',
            'completions',
            'average_watch_time_seconds',
            'drop_off_count',
        ]


class CourseStatsSerializer(serializers.Serializer):
    """Aggregated course statistics for admin."""
    
    total_enrollments = serializers.IntegerField()
    active_enrollments = serializers.IntegerField()
    total_completions = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_watch_time_hours = serializers.FloatField()


# -----------------------------------------------------------------
# Free Enrollment Serializer
# -----------------------------------------------------------------

class FreeEnrollSerializer(serializers.Serializer):
    """Input serializer for free course enrollment."""
    pass  # No input needed, course slug comes from URL


# -----------------------------------------------------------------
# Admin Serializers
# -----------------------------------------------------------------

class CourseAdminSerializer(serializers.ModelSerializer):
    """Full course serializer for admin CRUD."""
    
    class Meta:
        model = Course
        fields = '__all__'


class LessonAdminSerializer(serializers.ModelSerializer):
    """Full lesson serializer for admin CRUD."""
    
    class Meta:
        model = Lesson
        fields = '__all__'


# -----------------------------------------------------------------
# Quiz & MCQ Serializers
# -----------------------------------------------------------------

class MCQSerializer(serializers.ModelSerializer):
    """
    MCQ serializer for quiz display.
    
    SECURITY: Does NOT include correct_option or explanation
    until after submission.
    """
    
    class Meta:
        model = MCQ
        fields = [
            'id',
            'question',
            'order',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'difficulty',
            'topic',
        ]


class MCQWithAnswerSerializer(serializers.ModelSerializer):
    """
    MCQ serializer WITH correct answer and explanation.
    
    Only returned AFTER quiz submission.
    """
    
    class Meta:
        model = MCQ
        fields = [
            'id',
            'question',
            'order',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_option',
            'explanation',
            'difficulty',
            'topic',
        ]


class QuizSerializer(serializers.ModelSerializer):
    """
    Quiz serializer for lesson quiz display.
    
    Includes questions WITHOUT answers.
    """
    
    questions = MCQSerializer(many=True, read_only=True)
    question_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'total_questions',
            'passing_score',
            'time_limit_seconds',
            'question_count',
            'questions',
        ]


class QuizWithAnswersSerializer(serializers.ModelSerializer):
    """
    Quiz serializer WITH answers.
    
    Only returned after quiz submission for review.
    """
    
    questions = MCQWithAnswerSerializer(many=True, read_only=True)
    question_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'total_questions',
            'passing_score',
            'time_limit_seconds',
            'question_count',
            'questions',
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """
    Quiz attempt result serializer.
    """
    
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    lesson_title = serializers.CharField(source='quiz.lesson.title', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id',
            'quiz_title',
            'lesson_title',
            'score',
            'correct_count',
            'total_questions',
            'passed',
            'started_at',
            'completed_at',
            'time_taken_seconds',
        ]


class QuizSubmitSerializer(serializers.Serializer):
    """
    Input serializer for quiz submission.
    
    Expected format:
    {
        "answers": {
            "question_id_1": "A",
            "question_id_2": "B",
            ...
        }
    }
    """
    
    answers = serializers.DictField(
        child=serializers.CharField(max_length=1),
        help_text="Map of question ID to selected option (A/B/C/D)"
    )
    
    def validate_answers(self, value):
        """Validate answer format."""
        valid_options = {'A', 'B', 'C', 'D'}
        for question_id, answer in value.items():
            if answer.upper() not in valid_options:
                raise serializers.ValidationError(
                    f"Invalid answer '{answer}' for question {question_id}. "
                    f"Must be A, B, C, or D."
                )
        return {k: v.upper() for k, v in value.items()}


class QuizAttemptResultSerializer(serializers.Serializer):
    """
    Output serializer for quiz submission result.
    
    Includes:
    - Score and pass/fail status
    - Correct answers with explanations
    - Per-question results
    """
    
    attempt = QuizAttemptSerializer()
    quiz = QuizWithAnswersSerializer()
    user_answers = serializers.DictField()
    question_results = serializers.ListField(
        child=serializers.DictField()
    )


class LessonQuizStatusSerializer(serializers.Serializer):
    """
    Status of user's quiz progress for a lesson.
    """
    
    has_quiz = serializers.BooleanField()
    quiz_id = serializers.UUIDField(allow_null=True)
    attempts_count = serializers.IntegerField()
    best_score = serializers.IntegerField(allow_null=True)
    passed = serializers.BooleanField()
    last_attempt_at = serializers.DateTimeField(allow_null=True)


# -----------------------------------------------------------------
# Final Course Quiz Serializers
# -----------------------------------------------------------------

class CourseMCQSerializer(serializers.ModelSerializer):
    """MCQ serializer for final course quiz (no answers)."""
    
    class Meta:
        from .models import CourseMCQ
        model = CourseMCQ
        fields = [
            'id',
            'question',
            'order',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'difficulty',
            'topic',
        ]


class CourseMCQWithAnswerSerializer(serializers.ModelSerializer):
    """MCQ serializer with answers (after submission)."""
    
    class Meta:
        from .models import CourseMCQ
        model = CourseMCQ
        fields = [
            'id',
            'question',
            'order',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_option',
            'explanation',
            'difficulty',
            'topic',
        ]


class CourseQuizSerializer(serializers.ModelSerializer):
    """Final course quiz serializer (no answers)."""
    
    questions = CourseMCQSerializer(many=True, read_only=True)
    question_count = serializers.ReadOnlyField()
    
    class Meta:
        from .models import CourseQuiz
        model = CourseQuiz
        fields = [
            'id',
            'title',
            'description',
            'total_questions',
            'passing_score',
            'time_limit_seconds',
            'question_count',
            'questions',
        ]


class CourseQuizWithAnswersSerializer(serializers.ModelSerializer):
    """Final course quiz with answers (after submission)."""
    
    questions = CourseMCQWithAnswerSerializer(many=True, read_only=True)
    question_count = serializers.ReadOnlyField()
    
    class Meta:
        from .models import CourseQuiz
        model = CourseQuiz
        fields = [
            'id',
            'title',
            'description',
            'total_questions',
            'passing_score',
            'time_limit_seconds',
            'question_count',
            'questions',
        ]


class CourseQuizAttemptSerializer(serializers.ModelSerializer):
    """Final course quiz attempt serializer."""
    
    quiz_title = serializers.CharField(source='course_quiz.title', read_only=True)
    course_title = serializers.CharField(source='course_quiz.course.title', read_only=True)
    
    class Meta:
        from .models import CourseQuizAttempt
        model = CourseQuizAttempt
        fields = [
            'id',
            'quiz_title',
            'course_title',
            'score',
            'correct_count',
            'total_questions',
            'passed',
            'started_at',
            'completed_at',
            'time_taken_seconds',
        ]


class CourseQuizSubmitSerializer(serializers.Serializer):
    """Input serializer for final course quiz submission."""
    
    answers = serializers.DictField(
        child=serializers.CharField(max_length=1),
        help_text="Map of question ID to selected option (A/B/C/D)"
    )
    
    def validate_answers(self, value):
        valid_options = {'A', 'B', 'C', 'D'}
        for question_id, answer in value.items():
            if answer.upper() not in valid_options:
                raise serializers.ValidationError(
                    f"Invalid answer '{answer}' for question {question_id}. "
                    f"Must be A, B, C, or D."
                )
        return {k: v.upper() for k, v in value.items()}
