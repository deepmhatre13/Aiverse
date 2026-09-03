"""
Serializers for learner app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery, LearnerProfile, LearningPath
from learn.models import Lesson

User = get_user_model()


class MasteryVectorSerializer(serializers.Serializer):
    """Serializer for mastery vector."""
    concept_tag = serializers.CharField()
    mastery_score = serializers.FloatField()
    is_struggling = serializers.BooleanField()
    quiz_attempts = serializers.IntegerField()
    coding_attempts = serializers.IntegerField()


class LessonRecommendationSerializer(serializers.Serializer):
    """Serializer for lesson recommendations."""
    lesson_id = serializers.IntegerField()
    title = serializers.CharField()
    concept_tag = serializers.CharField()
    estimated_minutes = serializers.IntegerField()
    difficulty = serializers.CharField()
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()


class LearningPathSerializer(serializers.Serializer):
    """Serializer for learning path response."""
    ordered_lessons = LessonRecommendationSerializer(many=True)
    current_focus = serializers.CharField()
    estimated_completion_hours = serializers.FloatField()
    mastery_vector = serializers.DictField()
    user_id = serializers.IntegerField()


class KnowledgeGapSerializer(serializers.Serializer):
    """Serializer for knowledge gap objects."""
    concept_tag = serializers.CharField()
    mastery_score = serializers.FloatField()
    quiz_attempts = serializers.IntegerField()
    coding_attempts = serializers.IntegerField()
    suggested_actions = serializers.ListField(child=serializers.CharField())
    priority = serializers.CharField()


class KnowledgeGapWidgetSerializer(serializers.Serializer):
    """Serializer for knowledge gap dashboard widget."""
    gaps = KnowledgeGapSerializer(many=True)
    total_gaps = serializers.IntegerField()


class ConceptMasterySerializer(serializers.ModelSerializer):
    """Serializer for ConceptMastery model."""
    concept_tag_display = serializers.CharField(source='get_concept_tag_display', read_only=True)
    is_knowledge_gap = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ConceptMastery
        fields = [
            'id', 'user', 'concept_tag', 'concept_tag_display',
            'quiz_mastery', 'coding_mastery', 'video_completion_rate',
            'mastery_score', 'bkt_trace', 'quiz_attempts', 'coding_attempts',
            'is_struggling', 'is_knowledge_gap', 'last_updated', 'first_seen'
        ]
        read_only_fields = ['user', 'last_updated', 'first_seen']


class LearnerProfileSerializer(serializers.ModelSerializer):
    """Serializer for LearnerProfile model."""
    estimated_skill_level_display = serializers.CharField(source='get_estimated_skill_level_display', read_only=True)
    
    class Meta:
        model = LearnerProfile
        fields = [
            'id', 'user', 'estimated_skill_level', 'estimated_skill_level_display',
            'overall_mastery', 'avg_session_duration_minutes', 'total_sessions',
            'total_lessons_completed', 'total_problems_solved', 'total_quizzes_passed',
            'engagement_score', 'frustration_score', 'dropout_risk', 'learner_ability',
            'streak_days', 'learning_velocity', 'preferred_content_type',
            'preferred_difficulty', 'weak_concepts', 'strong_concepts',
            'last_active', 'last_updated', 'created_at'
        ]
        read_only_fields = ['user', 'last_updated', 'created_at']


class LearningPathModelSerializer(serializers.ModelSerializer):
    """Serializer for LearningPath model."""
    class Meta:
        model = LearningPath
        fields = ['id', 'user', 'ordered_lesson_ids', 'generated_at', 'is_adaptive']
        read_only_fields = ['user', 'generated_at']
class MasteryHistorySerializer(serializers.Serializer):
    """Serializer for per-concept BKT mastery history.

    Returns the persisted BKT probability trace for a concept so the
    frontend can render mastery-over-time. Reuses the existing BKT trace
    stored on ConceptMastery — no recomputation or duplication.
    """
    trace = serializers.ListField(child=serializers.FloatField())
    concept_tag = serializers.CharField()
    current_mastery = serializers.FloatField()


class PrerequisiteStatusSerializer(serializers.Serializer):
    """Status of a single prerequisite concept."""
    concept = serializers.CharField()
    mastery = serializers.FloatField()
    readiness = serializers.CharField()  # satisfied | partially_mastered | missing | unknown
    status = serializers.CharField()  # satisfied | partial | missing | unknown


class PrerequisiteResolutionSerializer(serializers.Serializer):
    """Resolution of prerequisites for a concept."""
    concept = serializers.CharField()
    prerequisites = PrerequisiteStatusSerializer(many=True)
    recommended_next = serializers.ListField(child=serializers.CharField())