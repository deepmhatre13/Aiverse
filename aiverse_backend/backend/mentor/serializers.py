from rest_framework import serializers
from .models import MentorSession, MentorMessage


class MentorMessageSerializer(serializers.ModelSerializer):
    """Serializer for mentor messages. Ensures role is strictly validated."""
    
    class Meta:
        model = MentorMessage
        fields = ['id', 'session', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at', 'session']

    def validate_role(self, value):
        """Ensure role is exactly 'user' or 'assistant' (lowercase)."""
        if value not in ('user', 'assistant'):
            raise serializers.ValidationError(
                f"Role must be 'user' or 'assistant', not '{value}'"
            )
        return value


class MentorSessionSerializer(serializers.ModelSerializer):
    """Serializer for mentor sessions with nested messages."""
    messages = MentorMessageSerializer(many=True, read_only=True)
    # UUID is serialized as string automatically by DRF
    
    class Meta:
        model = MentorSession
        fields = ['id', 'created_at', 'last_active_at', 'messages']
        read_only_fields = ['id', 'created_at', 'last_active_at', 'messages']


class AskMentorSerializer(serializers.Serializer):
    """Input validation for asking a question to the mentor."""
    question = serializers.CharField(
        max_length=5000,
        min_length=3,
        help_text="User question (3-5000 chars)"
    )
    # user_level kept for backwards compatibility but IGNORED by backend
    # The mentor automatically infers depth from conversation context
    user_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced'],
        default='intermediate',
        required=False,
        help_text="DEPRECATED: depth is inferred from question and history"
    )
    # Problem-aware mentoring: optional problem slug to load problem context
    problem_slug = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional problem slug (e.g., 'credit-risk-modeling'). "
                  "When provided, the mentor becomes problem-aware and tailors "
                  "guidance to the specific ML challenge."
    )
    # Last submission score: optional float for score-aware mentoring
    last_score = serializers.FloatField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Optional last submission score (e.g., 0.72). "
                  "When provided with problem_slug, the mentor analyzes the "
                  "score relative to the threshold and suggests improvements."
    )

    def validate_question(self, value):
        """Ensure question is non-empty after trimming."""
        stripped = value.strip()
        if len(stripped) < 3:
            raise serializers.ValidationError("Question must be at least 3 characters long.")
        return stripped

    def validate_problem_slug(self, value):
        """Validate problem_slug format if provided."""
        if value:
            stripped = value.strip()
            # Basic slug format validation (lowercase, hyphens, alphanumeric)
            import re
            if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', stripped):
                raise serializers.ValidationError(
                    "Invalid problem slug format. Expected lowercase with hyphens "
                    "(e.g., 'credit-risk-modeling')."
                )
            return stripped
        return value


class MentorResponseSerializer(serializers.Serializer):
    """Response structure for mentor answers (informational, not stored as-is)."""
    explanation = serializers.CharField()
    example = serializers.CharField(allow_blank=True, required=False)
    follow_up_questions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )