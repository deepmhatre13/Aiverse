"""
Unified permission for lesson and lesson content (quiz) access.
"""
from rest_framework.permissions import BasePermission


class CanAccessLessonContent(BasePermission):
    """
    Unified permission: same logic for lesson detail and quiz endpoints.
    
    Rules:
    - Free course: allow
    - Not enrolled (paid): deny
    - First lesson: allow
    - Previous lesson not completed: deny
    """
    
    message = "Lesson locked. Complete previous lesson."
    
    def has_object_permission(self, request, view, obj):
        from .models import Lesson, Enrollment, LessonProgress
        
        lesson = obj if hasattr(obj, 'course') else getattr(obj, 'lesson', obj)
        course = lesson.course
        
        if course.is_free:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        if not Enrollment.objects.filter(
            user=request.user,
            course=course,
            status='active'
        ).exists():
            return False
        
        prev_lesson = Lesson.objects.filter(
            course=course,
            order__lt=lesson.order
        ).order_by('-order').first()
        if not prev_lesson:
            return True
        return LessonProgress.objects.filter(
            user=request.user,
            lesson=prev_lesson,
            is_completed=True
        ).exists()
