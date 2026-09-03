from rest_framework import serializers
from .models import Recommendation
from django.utils import timezone


class RecommendationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    course_slug = serializers.SerializerMethodField()
    concept_tag = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    final_score = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    why_badge = serializers.SerializerMethodField()
    mastery_after = serializers.SerializerMethodField()
    is_due_today = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            'id', 'recommendation_type', 'content_type', 'content_id', 'score',
            'reason', 'source', 'is_dismissed', 'is_clicked', 'generated_at',
            'expires_at', 'is_due_today', 'title', 'slug', 'course_slug',
            'concept_tag', 'difficulty', 'final_score', 'explanation',
            'why_badge', 'mastery_after'
        ]

    def _get_linked_content(self, obj):
        if obj.content_type == 'lesson':
            from learn.models import Lesson
            try:
                return Lesson.objects.select_related('course').get(id=obj.content_id)
            except Lesson.DoesNotExist:
                return None
        if obj.content_type in {'problem', 'coding_problem'}:
            from learn.models import CodingProblem
            try:
                return CodingProblem.objects.select_related('lesson__course').get(id=obj.content_id)
            except CodingProblem.DoesNotExist:
                return None
        return None

    def get_title(self, obj):
        content = self._get_linked_content(obj)
        if content is None:
            return None
        return getattr(content, 'title', None)

    def get_slug(self, obj):
        content = self._get_linked_content(obj)
        if content is None:
            return None
        return getattr(content, 'slug', None)

    def get_course_slug(self, obj):
        content = self._get_linked_content(obj)
        if content is None:
            return None
        course = getattr(content, 'course', None)
        if course is not None:
            return getattr(course, 'slug', None)
        if hasattr(content, 'lesson') and content.lesson:
            return getattr(content.lesson.course, 'slug', None)
        return None

    def get_concept_tag(self, obj):
        content = self._get_linked_content(obj)
        if content is None:
            return None
        return getattr(content, 'concept_tag', None)

    def get_difficulty(self, obj):
        content = self._get_linked_content(obj)
        if content is None:
            return None
        return getattr(content, 'difficulty', None)

    def get_final_score(self, obj):
        return float(obj.score or 0.0)

    def get_explanation(self, obj):
        return obj.reason

    def get_why_badge(self, obj):
        return None

    def get_mastery_after(self, obj):
        return None

    def get_is_due_today(self, obj):
        """Check if recommendation is due today."""
        if not obj.expires_at:
            return False
        return obj.expires_at.date() == timezone.now().date()
