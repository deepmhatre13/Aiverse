"""
Production-grade Course System API Views.

Strict API design with:
- Versioned endpoints (/api/v1/)
- Consistent JSON responses
- Proper access control
- Rating-based enrollment gating
- No frontend-based trust
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.throttling import UserRateThrottle
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.conf import settings
import stripe
import logging

from .models import (
    Course, Lesson, Enrollment, LessonProgress,
    Certificate, CourseRating, Payment,
    CourseAnalytics, Quiz, MCQ, QuizAttempt
)
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
    EnrollmentSerializer,
    EnrollmentProgressSerializer,
    ProgressUpdateSerializer,
    LessonCompleteSerializer,
    CertificateSerializer,
    CertificateVerifySerializer,
    CourseRatingSerializer,
    CourseRatingCreateSerializer,
    CreateCheckoutSessionSerializer,
    PaymentIntentSerializer,
    PaymentSerializer,
    CourseStatsSerializer,
    QuizSerializer,
    QuizWithAnswersSerializer,
    QuizAttemptSerializer,
    QuizSubmitSerializer,
    QuizAttemptResultSerializer,
    LessonQuizStatusSerializer,
    MCQWithAnswerSerializer,
)
from .tasks import generate_certificate_task, generate_quiz_mcqs_task

logger = logging.getLogger(__name__)

# Configure Stripe (optional when Razorpay is used)
if getattr(settings, 'STRIPE_SECRET_KEY', ''):
    stripe.api_key = settings.STRIPE_SECRET_KEY


# -----------------------------------------------------------------
# Pagination
# -----------------------------------------------------------------

class StandardPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class LessonPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


# -----------------------------------------------------------------
# Throttling
# -----------------------------------------------------------------

class PaymentThrottle(UserRateThrottle):
    rate = None


# -----------------------------------------------------------------
# Course Views
# -----------------------------------------------------------------

class CourseListView(APIView):
    """
    List all published courses with filtering.
    
    GET /api/v1/courses/
    
    Query params:
    - level: beginner|intermediate|advanced|expert
    - is_free: true|false
    - track: track_slug
    - search: search query
    - ordering: created_at|-created_at|rating|-rating|students|-students
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        courses = Course.objects.filter(is_published=True)
        
        # Filter by level
        level = request.query_params.get('level')
        if level:
            courses = courses.filter(level=level)
        
        # Filter by free/paid
        is_free = request.query_params.get('is_free')
        if is_free is not None:
            is_free_bool = is_free.lower() in ['true', '1', 'yes']
            courses = courses.filter(is_free=is_free_bool)
        
        # Filter by track
        track_slug = request.query_params.get('track')
        if track_slug:
            courses = courses.filter(track__slug=track_slug)
        
        # Search
        search = request.query_params.get('search')
        if search:
            courses = courses.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__contains=[search])
            )
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        valid_orderings = {
            'created_at': 'created_at',
            '-created_at': '-created_at',
            'rating': 'rating_average',
            '-rating': '-rating_average',
            'students': 'students_count',
            '-students': '-students_count',
            'price': 'price',
            '-price': '-price',
        }
        if ordering in valid_orderings:
            courses = courses.order_by(valid_orderings[ordering])
        
        # Paginate
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(courses, request)
        
        serializer = CourseListSerializer(
            paginated,
            many=True,
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)


class FreeCourseListView(APIView):
    """
    List only free published courses.
    
    GET /api/v1/courses/free/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        courses = Course.objects.filter(
            is_published=True,
            is_free=True
        ).order_by('-created_at')
        
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(courses, request)
        
        serializer = CourseListSerializer(
            paginated,
            many=True,
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)


class PaidCourseListView(APIView):
    """
    List only paid published courses.
    
    GET /api/v1/courses/paid/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        courses = Course.objects.filter(
            is_published=True,
            is_paid=True
        ).order_by('-created_at')
        
        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(courses, request)
        
        serializer = CourseListSerializer(
            paginated,
            many=True,
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)


class CourseDetailView(APIView):
    """
    Get detailed course information with lessons.
    
    GET /api/v1/courses/{slug}/
    
    Returns:
    - Course details
    - Lessons list (with access status)
    - Enrollment status (if authenticated)
    - Progress (if enrolled)
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        serializer = CourseDetailSerializer(course, context={'request': request})
        
        response_data = {
            'course': serializer.data,
            'is_enrolled': serializer.data.get('is_enrolled', False),
            'is_locked': serializer.data.get('is_locked', False),
            'progress': serializer.data.get('progress'),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class CourseLessonsView(APIView):
    """
    Get all lessons for a course (curriculum).
    
    GET /api/v1/courses/{slug}/lessons/
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        lessons = course.lessons.all().order_by('order')
        
        serializer = LessonListSerializer(
            lessons,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'course_id': str(course.id),
            'course_title': course.title,
            'total_lessons': course.total_lessons,
            'lessons': serializer.data,
        }, status=status.HTTP_200_OK)


# -----------------------------------------------------------------
# Lesson Views
# -----------------------------------------------------------------

def _can_access_lesson_sequential(user, course, lesson):
    """
    Enforce sequential lesson unlock.
    - Free course: allow
    - First lesson: allow
    - Else: previous lesson must be completed
    Returns (allowed: bool, message: str|None)
    """
    if course.is_free:
        return True, None
    prev_lesson = Lesson.objects.filter(
        course=course, order__lt=lesson.order
    ).order_by('-order').first()
    if not prev_lesson:
        return True, None
    prev_completed = LessonProgress.objects.filter(
        user=user,
        lesson=prev_lesson,
        is_completed=True
    ).exists()
    if not prev_completed:
        return False, 'Complete the previous lesson first to unlock this one.'
    return True, None


class LessonDetailView(APIView):
    """
    Watch a lesson (with access control).
    
    GET /api/v1/courses/{course_slug}/lessons/{lesson_slug}/
    
    Access rules:
    1. Preview lessons: Always accessible
    2. Free courses: Requires authentication (no sequential lock)
    3. Paid courses: Requires active enrollment + sequential unlock
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_slug, lesson_slug):
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)
        
        has_access = False
        enrollment = None
        
        if lesson.is_preview:
            has_access = True
        elif request.user.is_staff or request.user.is_superuser:
            has_access = True
        elif course.is_free:
            has_access = True
            enrollment, _ = Enrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={
                    'status': 'active',
                    'activated_at': timezone.now()
                }
            )
        else:
            enrollment = Enrollment.objects.filter(
                user=request.user,
                course=course,
                status='active'
            ).first()
            has_access = enrollment is not None
        
        if not has_access:
            return Response({
                'error': 'Access denied',
                'message': 'Purchase the course to access this lesson.',
                'course_slug': course.slug,
                'is_preview': False,
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Sequential lock: previous lesson must be completed (paid courses)
        seq_ok, seq_message = _can_access_lesson_sequential(
            request.user, course, lesson
        )
        if not seq_ok:
            return Response({
                'error': 'Lesson locked',
                'message': seq_message or 'Complete the previous lesson first.',
                'course_slug': course.slug,
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last accessed
        if enrollment:
            enrollment.last_accessed_at = timezone.now()
            enrollment.save(update_fields=['last_accessed_at'])
        
        serializer = LessonDetailSerializer(lesson, context={'request': request})
        
        return Response({
            'lesson': serializer.data,
            'course': {
                'id': str(course.id),
                'title': course.title,
                'slug': course.slug,
            }
        }, status=status.HTTP_200_OK)


class LessonProgressView(APIView):
    """
    Update lesson progress.
    
    POST /api/v1/courses/{course_slug}/lessons/{lesson_slug}/progress/
    
    Body:
    {
        "watch_time_seconds": 120,
        "last_position_seconds": 115,
        "is_completed": false
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_slug, lesson_slug):
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)
        
        serializer = ProgressUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create enrollment
        enrollment = None
        if course.is_free:
            enrollment, _ = Enrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={
                    'status': 'active',
                    'activated_at': timezone.now()
                }
            )
        else:
            enrollment = Enrollment.objects.filter(
                user=request.user,
                course=course,
                status='active'
            ).first()
            
            if not enrollment and not lesson.is_preview:
                return Response({
                    'error': 'Not enrolled',
                    'message': 'Purchase the course to track progress.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Sequential lock: must have access to lesson
        seq_ok, seq_message = _can_access_lesson_sequential(
            request.user, course, lesson
        )
        if not seq_ok:
            return Response({
                'error': 'Lesson locked',
                'message': seq_message or 'Complete the previous lesson first.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        is_completed = serializer.validated_data.get('is_completed', False)
        watch_sec = serializer.validated_data.get('watch_time_seconds', 0)
        last_pos = serializer.validated_data.get('last_position_seconds', 0)
        
        progress, created = LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'enrollment': enrollment,
                'watch_time_seconds': watch_sec,
                'last_position_seconds': last_pos,
                'is_completed': is_completed,
                'completed_at': timezone.now() if is_completed else None,
            }
        )
        
        # Recalculate enrollment progress
        if enrollment:
            completion_percentage = enrollment.recalculate_progress()
            
            # Check for certificate
            if completion_percentage >= 100 and not enrollment.certificate_issued:
                generate_certificate_task.delay(str(enrollment.id))
        
        return Response({
            'is_completed': progress.is_completed,
            'watch_time_seconds': progress.watch_time_seconds,
            'last_position_seconds': progress.last_position_seconds,
            'course_progress': float(enrollment.completion_percentage) if enrollment else 0,
        }, status=status.HTTP_200_OK)


class LessonCompleteView(APIView):
    """
    Mark lesson as complete.
    
    POST /api/v1/lessons/{lesson_id}/complete/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        course = lesson.course
        
        serializer = LessonCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get enrollment
        enrollment = None
        if course.is_free:
            enrollment, _ = Enrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={
                    'status': 'active',
                    'activated_at': timezone.now()
                }
            )
        else:
            enrollment = Enrollment.objects.filter(
                user=request.user,
                course=course,
                status='active'
            ).first()
            
            if not enrollment:
                return Response({
                    'error': 'Not enrolled',
                    'message': 'Purchase the course to mark lessons complete.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Mark complete
        progress, _ = LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'enrollment': enrollment,
                'is_completed': True,
                'completed_at': timezone.now(),
                'watch_time_seconds': serializer.validated_data.get('watch_time_seconds', 0),
            }
        )
        
        # Recalculate progress
        completion_percentage = enrollment.recalculate_progress()
        
        # Check for certificate
        certificate_ready = False
        if completion_percentage >= 100 and not enrollment.certificate_issued:
            generate_certificate_task.delay(str(enrollment.id))
            certificate_ready = True
        
        return Response({
            'is_completed': True,
            'completion_percentage': float(completion_percentage),
            'lessons_completed': enrollment.lessons_completed,
            'total_lessons': course.total_lessons,
            'certificate_ready': certificate_ready,
        }, status=status.HTTP_200_OK)


# -----------------------------------------------------------------
# Enrollment Views
# -----------------------------------------------------------------

class EnrollmentListView(APIView):
    """
    List user's enrollments.
    
    GET /api/v1/enrollments/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        enrollments = Enrollment.objects.filter(
            user=request.user
        ).select_related('course').order_by('-enrolled_at')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            enrollments = enrollments.filter(status=status_filter)
        
        serializer = EnrollmentSerializer(enrollments, many=True)
        
        return Response({
            'enrollments': serializer.data,
            'total_active': enrollments.filter(status='active').count(),
            'total_completed': enrollments.filter(completion_percentage=100).count(),
        }, status=status.HTTP_200_OK)


class EnrollFreeView(APIView):
    """
    Enroll in a free course.
    
    POST /api/v1/courses/{slug}/enroll/
    
    Only for free courses. Paid courses must go through payment flow.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        # Verify course is free
        if course.is_paid:
            return Response({
                'error': 'Paid course',
                'message': 'This course requires payment. Use the payment endpoint.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rating requirement
        if not course.user_meets_rating_requirement(request.user):
            return Response({
                'error': 'Rating requirement not met',
                'message': f'Requires {course.required_rating} rating. Your rating: {request.user.rating}',
                'required_rating': course.required_rating,
                'user_rating': request.user.rating,
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'status': 'active',
                'activated_at': timezone.now(),
            }
        )
        
        if not created and enrollment.status == 'active':
            return Response({
                'message': 'Already enrolled',
                'enrollment_id': str(enrollment.id),
            }, status=status.HTTP_200_OK)
        
        # Ensure active
        enrollment.status = 'active'
        enrollment.activated_at = timezone.now()
        enrollment.save()
        
        # Update course stats
        course.update_stats()
        
        return Response({
            'message': 'Successfully enrolled',
            'enrollment_id': str(enrollment.id),
            'course': {
                'id': str(course.id),
                'title': course.title,
                'slug': course.slug,
            }
        }, status=status.HTTP_201_CREATED)


class CourseProgressView(APIView):
    """
    Get user's progress in a course.
    
    GET /api/v1/courses/{slug}/progress/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=course
            )
        except Enrollment.DoesNotExist:
            return Response({
                'error': 'Not enrolled',
                'message': 'You are not enrolled in this course.',
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get lesson progress
        lesson_progress = LessonProgress.objects.filter(
            user=request.user,
            lesson__course=course
        ).select_related('lesson').order_by('lesson__order')
        
        lessons_data = []
        for lp in lesson_progress:
            lessons_data.append({
                'lesson_id': str(lp.lesson.id),
                'lesson_slug': lp.lesson.slug,
                'lesson_title': lp.lesson.title,
                'order': lp.lesson.order,
                'is_completed': lp.is_completed,
                'watch_time_seconds': lp.watch_time_seconds,
            })
        
        return Response({
            'course': {
                'id': str(course.id),
                'title': course.title,
                'slug': course.slug,
            },
            'completion_percentage': float(enrollment.completion_percentage),
            'lessons_completed': enrollment.lessons_completed,
            'total_lessons': course.total_lessons,
            'certificate_issued': enrollment.certificate_issued,
            'lessons': lessons_data,
        }, status=status.HTTP_200_OK)


# -----------------------------------------------------------------
# Certificate Views
# -----------------------------------------------------------------

class CertificateListView(APIView):
    """
    List user's certificates.
    
    GET /api/v1/certificates/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        certificates = Certificate.objects.filter(
            user=request.user
        ).select_related('course').order_by('-issued_at')
        
        serializer = CertificateSerializer(certificates, many=True)
        
        return Response({
            'certificates': serializer.data,
            'total': certificates.count(),
        }, status=status.HTTP_200_OK)


class CertificateVerifyView(APIView):
    """
    Public certificate verification.
    
    GET /api/v1/certificates/verify/{certificate_id}/
    
    No authentication required - public verification endpoint.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, certificate_id):
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            serializer = CertificateVerifySerializer(certificate)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Certificate.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Certificate not found',
                'message': 'No certificate exists with this ID.',
            }, status=status.HTTP_404_NOT_FOUND)


# -----------------------------------------------------------------
# Rating Views
# -----------------------------------------------------------------

class CourseRatingView(APIView):
    """
    Rate a course.
    
    POST /api/v1/courses/{slug}/rate/
    
    Body:
    {
        "rating": 5,
        "review": "Excellent course!"
    }
    
    Only enrolled users with active status can rate.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        """Get all ratings for a course."""
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        ratings = CourseRating.objects.filter(
            course=course
        ).select_related('user').order_by('-created_at')[:50]
        
        serializer = CourseRatingSerializer(ratings, many=True)
        
        return Response({
            'course_id': str(course.id),
            'average_rating': float(course.rating_average),
            'total_ratings': course.rating_count,
            'ratings': serializer.data,
        }, status=status.HTTP_200_OK)
    
    def post(self, request, slug):
        """Create or update rating."""
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        # Verify enrollment
        try:
            enrollment = Enrollment.objects.get(
                user=request.user,
                course=course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            return Response({
                'error': 'Not enrolled',
                'message': 'Only enrolled students can rate courses.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CourseRatingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update rating
        rating, created = CourseRating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={
                'enrollment': enrollment,
                'rating': serializer.validated_data['rating'],
                'review': serializer.validated_data.get('review', ''),
            }
        )
        
        return Response({
            'message': 'Rating saved' if created else 'Rating updated',
            'rating': CourseRatingSerializer(rating).data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# -----------------------------------------------------------------
# Payment Views
# -----------------------------------------------------------------

class CreateCheckoutSessionView(APIView):
    """
    Create Stripe Checkout Session for course purchase.
    
    POST /api/v1/payments/create-checkout-session/
    
    Body:
    {
        "course_slug": "machine-learning-fundamentals",
        "success_url": "https://...",  // optional
        "cancel_url": "https://..."    // optional
    }
    
    Returns Stripe checkout URL for redirect.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentThrottle]
    
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        course_slug = serializer.validated_data['course_slug']
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        
        # Verify course is paid
        if course.is_free:
            return Response({
                'error': 'Free course',
                'message': 'This course is free. Use the enroll endpoint.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rating requirement
        if not course.user_meets_rating_requirement(request.user):
            return Response({
                'error': 'Rating requirement not met',
                'message': f'Requires {course.required_rating} rating. Your rating: {request.user.rating}',
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already enrolled
        existing = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).first()
        
        if existing:
            return Response({
                'error': 'Already enrolled',
                'message': 'You are already enrolled in this course.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create pending enrollment
                enrollment, _ = Enrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'status': 'pending'}
                )
                
                if enrollment.status == 'active':
                    return Response({
                        'error': 'Already enrolled',
                        'message': 'You are already enrolled in this course.',
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # URLs
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
                success_url = serializer.validated_data.get(
                    'success_url',
                    f"{frontend_url}/learn/courses/{course.slug}?payment=success"
                )
                cancel_url = serializer.validated_data.get(
                    'cancel_url',
                    f"{frontend_url}/learn/courses/{course.slug}?payment=cancelled"
                )
                
                # Create Stripe Checkout Session
                checkout_session = stripe.checkout.Session.create(
                    mode='payment',
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': course.currency.lower(),
                            'product_data': {
                                'name': course.title,
                                'description': course.short_description or course.description[:200],
                                'images': [course.thumbnail] if course.thumbnail else [],
                            },
                            'unit_amount': int(course.price * 100),
                        },
                        'quantity': 1,
                    }],
                    metadata={
                        'user_id': str(request.user.id),
                        'course_id': str(course.id),
                        'enrollment_id': str(enrollment.id),
                    },
                    customer_email=request.user.email,
                    success_url=success_url,
                    cancel_url=cancel_url,
                )
                
                # Create Payment record
                payment = Payment.objects.create(
                    user=request.user,
                    enrollment=enrollment,
                    stripe_payment_intent_id=checkout_session.payment_intent or f"cs_{checkout_session.id}",
                    stripe_checkout_session_id=checkout_session.id,
                    amount=course.price,
                    currency=course.currency,
                    status='pending',
                    metadata={
                        'course_title': course.title,
                        'course_slug': course.slug,
                        'checkout_session_id': checkout_session.id,
                    }
                )
                
                return Response({
                    'checkout_url': checkout_session.url,
                    'session_id': checkout_session.id,
                }, status=status.HTTP_201_CREATED)
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({
                'error': 'Payment error',
                'message': 'Unable to create checkout session. Please try again.',
            }, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentIntentView(APIView):
    """
    Create Stripe PaymentIntent for custom payment form.
    
    POST /api/v1/payments/create-intent/
    
    Body:
    {
        "course_slug": "machine-learning-fundamentals"
    }
    
    Returns client_secret for Stripe Elements.
    """
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentThrottle]
    
    def post(self, request):
        serializer = PaymentIntentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        course_slug = serializer.validated_data['course_slug']
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        
        # Verify course is paid
        if course.is_free:
            return Response({
                'error': 'Free course',
                'message': 'This course is free.',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rating requirement
        if not course.user_meets_rating_requirement(request.user):
            return Response({
                'error': 'Rating requirement not met',
                'message': f'Requires {course.required_rating} rating.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already enrolled
        existing = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).first()
        
        if existing:
            return Response({
                'error': 'Already enrolled',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create pending enrollment
                enrollment, _ = Enrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'status': 'pending'}
                )
                
                # Create PaymentIntent
                amount_cents = int(course.price * 100)
                
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency=course.currency.lower(),
                    metadata={
                        'user_id': str(request.user.id),
                        'course_id': str(course.id),
                        'enrollment_id': str(enrollment.id),
                    },
                    receipt_email=request.user.email,
                )
                
                # Create Payment record
                payment = Payment.objects.create(
                    user=request.user,
                    enrollment=enrollment,
                    stripe_payment_intent_id=payment_intent.id,
                    stripe_client_secret=payment_intent.client_secret,
                    amount=course.price,
                    currency=course.currency,
                    status='pending',
                    metadata={
                        'course_title': course.title,
                        'course_slug': course.slug,
                    }
                )
                
                # Update enrollment
                enrollment.payment_reference = payment_intent.id
                enrollment.save(update_fields=['payment_reference'])
                
                return Response({
                    'payment_intent_id': payment_intent.id,
                    'client_secret': payment_intent.client_secret,
                    'amount': float(course.price),
                    'currency': course.currency,
                }, status=status.HTTP_201_CREATED)
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({
                'error': 'Payment error',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------------------
# Razorpay Payment Views
# -----------------------------------------------------------------

class CreateRazorpayOrderView(APIView):
    """
    Create Razorpay order for course purchase.

    POST /api/learn/payments/razorpay/create-order/

    Body:
    {
        "course_slug": "machine-learning-fundamentals"
    }

    Returns order_id, amount, currency, key_id for frontend Razorpay checkout.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentThrottle]

    def post(self, request):
        from .payment_utils import create_razorpay_order, is_razorpay_configured

        course_slug = request.data.get('course_slug')
        if not course_slug:
            return Response({'error': 'course_slug is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_razorpay_configured():
            return Response({
                'error': 'Razorpay not configured',
                'message': 'Payment gateway is not available.',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        course = get_object_or_404(Course, slug=course_slug, is_published=True)

        if course.is_free:
            return Response({
                'error': 'Free course',
                'message': 'This course is free. Use the enroll endpoint.',
            }, status=status.HTTP_400_BAD_REQUEST)

        if not course.user_meets_rating_requirement(request.user):
            return Response({
                'error': 'Rating requirement not met',
                'message': f'Requires {course.required_rating} rating.',
            }, status=status.HTTP_403_FORBIDDEN)

        existing = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).first()
        if existing:
            return Response({
                'error': 'Already enrolled',
                'message': 'You are already enrolled in this course.',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                enrollment, created = Enrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'status': 'pending'}
                )
                if enrollment.status == 'active':
                    return Response({
                        'error': 'Already enrolled',
                        'message': 'You are already enrolled.',
                    }, status=status.HTTP_400_BAD_REQUEST)

                amount_smallest = int(float(course.price) * 100)
                currency = getattr(course, 'currency', 'INR')

                result = create_razorpay_order(
                    amount_paise=amount_smallest,
                    currency=currency,
                    notes={
                        'user_id': str(request.user.id),
                        'course_id': str(course.id),
                        'enrollment_id': str(enrollment.id),
                    }
                )
                if not result:
                    return Response({
                        'error': 'Payment error',
                        'message': 'Unable to create order.',
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                enrollment.payment_reference = result['order_id']
                enrollment.save(update_fields=['payment_reference'])

                return Response({
                    'order_id': result['order_id'],
                    'amount': result['amount'],
                    'currency': result['currency'],
                    'key_id': result['key_id'],
                    'enrollment_id': str(enrollment.id),
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f'Razorpay order creation failed: {e}')
            return Response({
                'error': 'Payment error',
                'message': 'Unable to create order. Please try again.',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyRazorpayPaymentView(APIView):
    """
    Verify Razorpay payment and activate enrollment.

    POST /api/learn/payments/razorpay/verify/

    Body:
    {
        "order_id": "order_xxx",
        "payment_id": "pay_xxx",
        "signature": "xxx",
        "course_slug": "machine-learning-fundamentals"
    }
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentThrottle]

    def post(self, request):
        from .payment_utils import verify_razorpay_signature, is_razorpay_configured

        if not is_razorpay_configured():
            return Response({
                'error': 'Razorpay not configured',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        order_id = request.data.get('order_id')
        payment_id = request.data.get('payment_id')
        signature = request.data.get('signature')
        course_slug = request.data.get('course_slug')

        if not all([order_id, payment_id, signature, course_slug]):
            return Response({
                'error': 'Missing fields',
                'message': 'order_id, payment_id, signature, and course_slug are required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        if not verify_razorpay_signature(order_id, payment_id, signature):
            return Response({
                'error': 'Invalid signature',
                'message': 'Payment verification failed. Possible tampering.',
            }, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            payment_reference=order_id,
        ).first()

        if not enrollment:
            return Response({
                'error': 'Enrollment not found',
                'message': 'No matching enrollment. Please try the purchase flow again.',
            }, status=status.HTTP_404_NOT_FOUND)

        if enrollment.status == 'active':
            return Response({
                'message': 'Already enrolled',
                'enrollment_id': str(enrollment.id),
                'course_slug': course.slug,
            }, status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                enrollment.status = 'active'
                enrollment.is_paid = True
                enrollment.payment_reference = payment_id
                enrollment.activated_at = timezone.now()
                enrollment.purchased_at = timezone.now()
                enrollment.save(update_fields=['status', 'is_paid', 'payment_reference', 'activated_at', 'purchased_at'])

                course.update_stats()

                return Response({
                    'message': 'Payment successful',
                    'enrollment_id': str(enrollment.id),
                    'course_slug': course.slug,
                    'course_title': course.title,
                }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f'Razorpay verification failed: {e}')
            return Response({
                'error': 'Verification failed',
                'message': 'Could not complete enrollment. Please contact support.',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# Admin Views
# -----------------------------------------------------------------

class CourseAnalyticsView(APIView):
    """
    Get course analytics (admin only).
    
    GET /api/v1/admin/courses/{slug}/analytics/
    """
    
    permission_classes = [IsAdminUser]
    
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timezone.timedelta(days=days)
        
        analytics = CourseAnalytics.objects.filter(
            course=course,
            date__gte=start_date
        ).order_by('date')
        
        # Aggregate stats
        total_enrollments = Enrollment.objects.filter(course=course).count()
        active_enrollments = Enrollment.objects.filter(course=course, status='active').count()
        total_completions = Enrollment.objects.filter(course=course, completion_percentage=100).count()
        total_revenue = Payment.objects.filter(
            enrollment__course=course,
            status='succeeded'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_watch_time = LessonProgress.objects.filter(
            lesson__course=course
        ).aggregate(total=Sum('watch_time_seconds'))['total'] or 0
        
        return Response({
            'course_id': str(course.id),
            'course_title': course.title,
            'stats': {
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'total_completions': total_completions,
                'completion_rate': (total_completions / total_enrollments * 100) if total_enrollments > 0 else 0,
                'total_revenue': float(total_revenue),
                'average_rating': float(course.rating_average),
                'total_watch_time_hours': round(total_watch_time / 3600, 2),
            },
            'daily_analytics': [
                {
                    'date': a.date.isoformat(),
                    'views': a.views,
                    'enrollments': a.enrollments,
                    'completions': a.completions,
                    'revenue': float(a.revenue),
                }
                for a in analytics
            ]
        }, status=status.HTTP_200_OK)


# -----------------------------------------------------------------
# Quiz Views
# -----------------------------------------------------------------

class LessonQuizView(APIView):
    """
    Get quiz for a lesson.
    Uses same access logic as lesson detail: enrollment + sequential lock.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_slug, lesson_slug):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            course = Course.objects.get(slug=course_slug, is_published=True)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            lesson = Lesson.objects.select_related('course').get(
                course=course,
                slug=lesson_slug
            )
        except Lesson.DoesNotExist:
            return Response({'detail': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not course.is_free:
            if not Enrollment.objects.filter(
                user=user,
                course=course,
                status='active'
            ).exists():
                return Response({
                    'detail': 'Lesson locked. Enrollment required.',
                }, status=status.HTTP_403_FORBIDDEN)
        
        seq_ok, seq_message = _can_access_lesson_sequential(user, course, lesson)
        if not seq_ok:
            return Response({
                'detail': seq_message or 'Lesson locked. Complete previous lesson.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            quiz = lesson.quiz
        except Quiz.DoesNotExist:
            return Response({
                'has_quiz': False,
                'message': 'No quiz available for this lesson'
            }, status=status.HTTP_200_OK)
        
        # Get user's quiz status
        attempts = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz
        ).order_by('-started_at')
        
        best_attempt = attempts.filter(passed=True).first()
        last_attempt = attempts.first()
        
        serializer = QuizSerializer(quiz)
        
        return Response({
            'has_quiz': True,
            'quiz': serializer.data,
            'user_status': {
                'attempts_count': attempts.count(),
                'best_score': best_attempt.score if best_attempt else None,
                'passed': best_attempt is not None,
                'last_attempt_at': last_attempt.started_at if last_attempt else None,
            }
        }, status=status.HTTP_200_OK)


class QuizSubmitView(APIView):
    """
    Submit quiz answers.
    
    POST /api/v1/courses/{course_slug}/lessons/{lesson_slug}/quiz/submit/
    
    Body:
    {
        "answers": {
            "question_id": "A|B|C|D",
            ...
        }
    }
    
    Returns:
    - Score and pass/fail status
    - Correct answers with explanations
    - Updates lesson progress if passed
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_slug, lesson_slug):
        # Get lesson and quiz
        lesson = get_object_or_404(
            Lesson.objects.select_related('course'),
            course__slug=course_slug,
            slug=lesson_slug
        )
        
        try:
            quiz = lesson.quiz
        except Quiz.DoesNotExist:
            return Response({
                'error': 'No quiz',
                'message': 'No quiz available for this lesson'
            }, status=status.HTTP_404_NOT_FOUND)
        
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        course = lesson.course
        if not course.is_free:
            enrollment = Enrollment.objects.filter(
                user=user,
                course=course,
                status='active'
            ).first()
            if not enrollment:
                return Response({
                    'detail': 'Lesson locked. Enrollment required.',
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            enrollment, _ = Enrollment.objects.get_or_create(
                user=user,
                course=course,
                defaults={'status': 'active', 'activated_at': timezone.now()}
            )
        
        seq_ok, seq_message = _can_access_lesson_sequential(user, course, lesson)
        if not seq_ok:
            return Response({
                'detail': seq_message or 'Lesson locked. Complete previous lesson.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = QuizSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        answers = serializer.validated_data['answers']
        
        # Create quiz attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            enrollment=enrollment,
            answers=answers,
        )
        
        # Calculate score
        attempt.calculate_score()
        
        # Build question results
        questions = quiz.questions.all().order_by('order')
        question_results = []
        
        for q in questions:
            user_answer = answers.get(str(q.id))
            is_correct = user_answer == q.correct_option if user_answer else False
            
            question_results.append({
                'question_id': str(q.id),
                'question': q.question,
                'user_answer': user_answer,
                'correct_answer': q.correct_option,
                'is_correct': is_correct,
                'explanation': q.explanation,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
            })
        
        # Update lesson progress if passed
        if attempt.passed:
            progress, _ = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson,
                defaults={'enrollment': enrollment}
            )
            
            # Check if video is also completed (>= 90% watched)
            video_completed = False
            if lesson.duration_minutes > 0:
                watch_percentage = (progress.watch_time_seconds / (lesson.duration_minutes * 60)) * 100
                video_completed = watch_percentage >= 90
            else:
                video_completed = True  # No video = auto-complete
            
            # Mark lesson complete only if both video and quiz are done
            if video_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save()
                
                # Update enrollment progress
                if enrollment:
                    enrollment.recalculate_progress()
                    
                    # Trigger certificate if 100% complete
                    if enrollment.completion_percentage >= 100:
                        generate_certificate_task.delay(enrollment.id)
        
        return Response({
            'attempt': QuizAttemptSerializer(attempt).data,
            'quiz': QuizWithAnswersSerializer(quiz).data,
            'user_answers': answers,
            'question_results': question_results,
            'lesson_completed': attempt.passed,
        }, status=status.HTTP_201_CREATED)


class QuizAttemptHistoryView(APIView):
    """
    Get user's quiz attempt history.
    
    GET /api/v1/quiz-attempts/
    
    Query params:
    - course: Filter by course slug
    - limit: Limit results (default 20)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        attempts = QuizAttempt.objects.filter(
            user=request.user
        ).select_related('quiz__lesson__course').order_by('-started_at')
        
        # Filter by course
        course_slug = request.query_params.get('course')
        if course_slug:
            attempts = attempts.filter(quiz__lesson__course__slug=course_slug)
        
        # Limit
        limit = int(request.query_params.get('limit', 20))
        attempts = attempts[:limit]
        
        serializer = QuizAttemptSerializer(attempts, many=True)
        
        return Response({
            'attempts': serializer.data,
            'total': len(serializer.data),
        }, status=status.HTTP_200_OK)


class AdminGenerateQuizView(APIView):
    """
    Admin endpoint to generate/regenerate quiz for a lesson.
    
    POST /api/v1/admin/lessons/{lesson_id}/generate-quiz/
    
    Body (optional):
    {
        "num_questions": 5,
        "transcript": "Optional custom content for generation"
    }
    """
    
    permission_classes = [IsAdminUser]
    
    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        num_questions = request.data.get('num_questions', 5)
        transcript = request.data.get('transcript')
        
        # Delete existing quiz if present
        Quiz.objects.filter(lesson=lesson).delete()
        
        # Queue generation task
        task = generate_quiz_mcqs_task.delay(
            lesson_id=lesson.id,
            transcript=transcript,
            num_questions=num_questions
        )
        
        return Response({
            'status': 'queued',
            'task_id': str(task.id),
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'num_questions': num_questions,
        }, status=status.HTTP_202_ACCEPTED)


# -----------------------------------------------------------------
# Final Course Quiz Views
# -----------------------------------------------------------------

class CourseQuizView(APIView):
    """
    Get final quiz for a course.
    
    GET /api/v1/courses/{slug}/final-quiz/
    
    Only accessible after completing all lessons.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        from .models import CourseQuiz, CourseQuizAttempt
        from .serializers import CourseQuizSerializer
        
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        # Check enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).first()
        
        if not enrollment:
            return Response({
                'error': 'Not enrolled',
                'message': 'You must be enrolled to take the final quiz.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check lesson completion - all lessons must be done
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__course=course,
            is_completed=True
        ).count()
        
        total_lessons = course.total_lessons
        
        if completed_lessons < total_lessons:
            return Response({
                'has_quiz': False,
                'reason': 'lessons_incomplete',
                'completed_lessons': completed_lessons,
                'total_lessons': total_lessons,
                'message': f'Complete all {total_lessons} lessons to unlock the final quiz.'
            }, status=status.HTTP_200_OK)
        
        # Get or generate final quiz
        try:
            quiz = course.final_quiz
        except CourseQuiz.DoesNotExist:
            # Generate quiz asynchronously
            from .tasks import generate_final_quiz_task
            generate_final_quiz_task.delay(course.id)
            return Response({
                'has_quiz': False,
                'reason': 'generating',
                'message': 'Final quiz is being generated. Please check back in a few moments.'
            }, status=status.HTTP_200_OK)
        
        # Get user's quiz status
        attempts = CourseQuizAttempt.objects.filter(
            user=request.user,
            course_quiz=quiz
        ).order_by('-started_at')
        
        best_attempt = attempts.filter(passed=True).first()
        last_attempt = attempts.first()
        
        serializer = CourseQuizSerializer(quiz)
        
        return Response({
            'has_quiz': True,
            'quiz': serializer.data,
            'course': {
                'id': course.id,
                'title': course.title,
                'slug': course.slug,
            },
            'user_status': {
                'attempts_count': attempts.count(),
                'best_score': best_attempt.score if best_attempt else None,
                'passed': best_attempt is not None,
                'last_attempt_at': last_attempt.started_at if last_attempt else None,
            }
        }, status=status.HTTP_200_OK)


class CourseQuizSubmitView(APIView):
    """
    Submit final course quiz answers.
    
    POST /api/v1/courses/{slug}/final-quiz/submit/
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        from .models import CourseQuiz, CourseQuizAttempt
        from .serializers import (
            CourseQuizSubmitSerializer,
            CourseQuizAttemptSerializer,
            CourseQuizWithAnswersSerializer
        )
        
        course = get_object_or_404(Course, slug=slug, is_published=True)
        
        try:
            quiz = course.final_quiz
        except CourseQuiz.DoesNotExist:
            return Response({
                'error': 'No quiz',
                'message': 'Final quiz not available for this course.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).first()
        
        if not enrollment:
            return Response({
                'error': 'Not enrolled',
                'message': 'You must be enrolled to submit the quiz.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input
        serializer = CourseQuizSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        answers = serializer.validated_data['answers']
        
        # Create quiz attempt
        attempt = CourseQuizAttempt.objects.create(
            user=request.user,
            course_quiz=quiz,
            enrollment=enrollment,
            answers=answers,
        )
        
        # Calculate score (this also handles certificate generation)
        attempt.calculate_score()
        
        # Build question results
        questions = quiz.questions.all().order_by('order')
        question_results = []
        correct_count = 0
        
        for q in questions:
            user_answer = answers.get(str(q.id))
            is_correct = user_answer == q.correct_option if user_answer else False
            if is_correct:
                correct_count += 1
            
            question_results.append({
                'question_id': str(q.id),
                'question': q.question,
                'user_answer': user_answer,
                'correct_answer': q.correct_option,
                'is_correct': is_correct,
                'explanation': q.explanation,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
            })
        
        # Flat response for easy frontend consumption
        return Response({
            'score': attempt.score,
            'passed': attempt.passed,
            'correct_count': correct_count,
            'total_questions': questions.count(),
            'attempt_number': CourseQuizAttempt.objects.filter(
                user=request.user,
                course_quiz=quiz
            ).count(),
            'question_results': question_results,
            'user_answers': answers,
            'course_completed': attempt.passed,
            'certificate_pending': attempt.passed and not enrollment.certificate_issued,
            'certificate_url': enrollment.certificate.file.url if hasattr(enrollment, 'certificate') and enrollment.certificate and enrollment.certificate.file else None,
        }, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------------
# Lesson Progression Lock Views
# -----------------------------------------------------------------

class LessonAccessCheckView(APIView):
    """
    Check if user can access a specific lesson.
    
    GET /api/v1/courses/{course_slug}/lessons/{lesson_slug}/access/
    
    Returns:
    - is_accessible: boolean
    - reason: why access is denied (if applicable)
    - required_lesson: previous lesson that must be completed
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_slug, lesson_slug):
        lesson = get_object_or_404(
            Lesson.objects.select_related('course'),
            course__slug=course_slug,
            slug=lesson_slug
        )
        
        course = lesson.course
        
        # Preview lessons always accessible
        if lesson.is_preview:
            return Response({
                'is_accessible': True,
                'reason': 'preview_lesson'
            }, status=status.HTTP_200_OK)
        
        # Check enrollment for paid courses
        if not course.is_free:
            enrollment = Enrollment.objects.filter(
                user=request.user,
                course=course,
                status='active'
            ).first()
            if not enrollment:
                return Response({
                    'is_accessible': False,
                    'reason': 'enrollment_required',
                    'message': 'You must enroll in this course to access lessons'
                }, status=status.HTTP_200_OK)
        
        # Check progression lock
        # First lesson is always accessible
        if lesson.order == 1:
            return Response({
                'is_accessible': True,
                'reason': 'first_lesson'
            }, status=status.HTTP_200_OK)
        
        # Check if previous lesson is completed
        previous_lesson = Lesson.objects.filter(
            course=course,
            order=lesson.order - 1
        ).first()
        
        if not previous_lesson:
            return Response({
                'is_accessible': True,
                'reason': 'no_previous_lesson'
            }, status=status.HTTP_200_OK)
        
        # Check completion of previous lesson
        previous_progress = LessonProgress.objects.filter(
            user=request.user,
            lesson=previous_lesson,
            is_completed=True
        ).first()
        
        if not previous_progress:
            return Response({
                'is_accessible': False,
                'reason': 'previous_lesson_incomplete',
                'required_lesson': {
                    'id': previous_lesson.id,
                    'slug': previous_lesson.slug,
                    'title': previous_lesson.title,
                    'order': previous_lesson.order,
                },
                'message': f'Complete "{previous_lesson.title}" first'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'is_accessible': True,
            'reason': 'previous_completed'
        }, status=status.HTTP_200_OK)
