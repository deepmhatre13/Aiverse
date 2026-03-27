"""
Production-grade Course System URL Configuration.

API Design:
- Versioned: /api/v1/learn/
- RESTful endpoints
- Consistent naming

Public endpoints (AllowAny):
- GET /courses/
- GET /courses/{slug}/
- GET /courses/{slug}/lessons/
- GET /certificates/verify/{certificate_id}/

Authenticated endpoints:
- POST /courses/{slug}/enroll/
- GET /courses/{slug}/progress/
- GET /courses/{slug}/lessons/{slug}/
- POST /courses/{slug}/lessons/{slug}/progress/
- POST /lessons/{id}/complete/
- GET /enrollments/
- GET /certificates/
- POST /courses/{slug}/rate/
- POST /payments/create-checkout-session/
- POST /payments/create-intent/
- POST /payments/webhook/
- GET /payments/
"""

from django.urls import path
from .views import (
    # Course views
    CourseListView,
    CreateRazorpayOrderView,
    VerifyRazorpayPaymentView,
    FreeCourseListView,
    PaidCourseListView,
    CourseDetailView,
    CourseLessonsView,
    CourseProgressView,
    
    # Lesson views
    LessonDetailView,
    LessonProgressView,
    LessonCompleteView,
    
    # Enrollment views
    EnrollmentListView,
    EnrollFreeView,
    
    # Certificate views
    CertificateListView,
    CertificateVerifyView,
    
    # Rating views
    CourseRatingView,
    
    # Payment views
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    
    # (Receipts removed)
    
    # Admin views
    CourseAnalyticsView,
    
    # Quiz views
    LessonQuizView,
    QuizSubmitView,
    QuizAttemptHistoryView,
    AdminGenerateQuizView,
    LessonAccessCheckView,
    
    # Final quiz views
    CourseQuizView,
    CourseQuizSubmitView,
)
from .webhook import stripe_webhook

app_name = 'learn'

urlpatterns = [
    # ===== COURSES =====
    
    # List courses with filtering
    path('courses/', CourseListView.as_view(), name='course-list'),
    path('courses/free/', FreeCourseListView.as_view(), name='course-free-list'),
    path('courses/paid/', PaidCourseListView.as_view(), name='course-paid-list'),
    
    # Course detail
    path('courses/<slug:slug>/', CourseDetailView.as_view(), name='course-detail'),
    
    # Course lessons (curriculum)
    path('courses/<slug:slug>/lessons/', CourseLessonsView.as_view(), name='course-lessons'),
    
    # Course progress
    path('courses/<slug:slug>/progress/', CourseProgressView.as_view(), name='course-progress'),
    
    # Free course enrollment
    path('courses/<slug:slug>/enroll/', EnrollFreeView.as_view(), name='course-enroll'),
    
    # Course rating
    path('courses/<slug:slug>/rate/', CourseRatingView.as_view(), name='course-rate'),
    
    # ===== LESSONS =====
    
    # Lesson detail (watch)
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/',
        LessonDetailView.as_view(),
        name='lesson-detail'
    ),
    
    # Update lesson progress
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/progress/',
        LessonProgressView.as_view(),
        name='lesson-progress'
    ),
    
    # Mark lesson complete
    path('lessons/<int:lesson_id>/complete/', LessonCompleteView.as_view(), name='lesson-complete'),
    
    # ===== ENROLLMENTS =====
    
    path('enrollments/', EnrollmentListView.as_view(), name='enrollment-list'),
    
    # ===== CERTIFICATES =====
    
    path('certificates/', CertificateListView.as_view(), name='certificate-list'),
    path(
        'certificates/verify/<str:certificate_id>/',
        CertificateVerifyView.as_view(),
        name='certificate-verify'
    ),
    
    # ===== PAYMENTS =====
    
    # Stripe Checkout (recommended)
    path(
        'payments/create-checkout-session/',
        CreateCheckoutSessionView.as_view(),
        name='create-checkout-session'
    ),
    
    # Stripe Elements (custom form)
    path(
        'payments/create-intent/',
        CreatePaymentIntentView.as_view(),
        name='create-payment-intent'
    ),
    
    # Stripe webhook (POST only, no auth)
    path('payments/webhook/', stripe_webhook, name='stripe-webhook'),

    # Razorpay
    path('payments/razorpay/create-order/', CreateRazorpayOrderView.as_view(), name='razorpay-create-order'),
    path('payments/razorpay/verify/', VerifyRazorpayPaymentView.as_view(), name='razorpay-verify'),
    
    # (Receipts removed)
    
    # ===== ADMIN =====
    
    path(
        'admin/courses/<slug:slug>/analytics/',
        CourseAnalyticsView.as_view(),
        name='course-analytics'
    ),
    
    # Admin quiz generation
    path(
        'admin/lessons/<int:lesson_id>/generate-quiz/',
        AdminGenerateQuizView.as_view(),
        name='admin-generate-quiz'
    ),
    
    # ===== QUIZZES =====
    
    # Get lesson quiz
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/quiz/',
        LessonQuizView.as_view(),
        name='lesson-quiz'
    ),
    
    # Submit quiz answers
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/quiz/submit/',
        QuizSubmitView.as_view(),
        name='quiz-submit'
    ),
    
    # Check lesson access (progression lock)
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/access/',
        LessonAccessCheckView.as_view(),
        name='lesson-access-check'
    ),
    
    # Quiz attempt history
    path('quiz-attempts/', QuizAttemptHistoryView.as_view(), name='quiz-attempts'),
    
    # ===== FINAL COURSE QUIZ =====
    
    # Get final course quiz
    path('courses/<slug:slug>/final-quiz/', CourseQuizView.as_view(), name='course-final-quiz'),
    
    # Submit final course quiz
    path('courses/<slug:slug>/final-quiz/submit/', CourseQuizSubmitView.as_view(), name='course-final-quiz-submit'),
]
