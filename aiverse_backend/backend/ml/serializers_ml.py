"""
Serializers for ML evaluation and submission.
Handles validation and API responses.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models_ml import Problem, Submission, Leaderboard


class ProblemSerializer(serializers.ModelSerializer):
    """Problem definition serializer."""
    
    class Meta:
        model = Problem
        fields = [
            'slug', 'title', 'description', 'task_type',
            'default_metric', 'allowed_metrics', 'submission_threshold',
            'difficulty'
        ]


class EvaluationRequestSerializer(serializers.Serializer):
    """Request schema for evaluation endpoint."""
    
    code = serializers.CharField(
        required=True,
        help_text="Python code with train_and_predict(X_train, y_train, X_test) function"
    )
    metric = serializers.CharField(
        required=False,
        default=None,
        help_text="Optional metric override (uses default if not specified)"
    )
    
    def validate_code(self, value):
        """Validate code is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty")
        return value


class EvaluationResponseSerializer(serializers.Serializer):
    """Response schema for successful evaluation."""
    
    status = serializers.CharField()  # "success"
    metric = serializers.CharField()
    score = serializers.FloatField()
    threshold = serializers.FloatField(allow_null=True)
    meets_threshold = serializers.BooleanField()


class EvaluationErrorSerializer(serializers.Serializer):
    """Response schema for evaluation error."""
    
    status = serializers.CharField()  # "error"
    error_type = serializers.CharField()
    message = serializers.CharField()


class SubmissionRequestSerializer(serializers.Serializer):
    """Request schema for submission endpoint."""
    
    code = serializers.CharField(required=True)
    metric = serializers.CharField(required=False, default=None)
    
    def validate_code(self, value):
        """Validate code is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty")
        return value


class SubmissionSerializer(serializers.ModelSerializer):
    """Full submission record serializer."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    score = serializers.SerializerMethodField()  # Alias for public_score
    
    class Meta:
        model = Submission
        fields = [
            'id', 'username', 'problem_title', 'code', 'metric', 'score',
            'status', 'rank', 'is_best', 'created_at', 'error_message'
        ]
        read_only_fields = ['id', 'status', 'score', 'rank', 'error_message', 'code']
    
    def get_score(self, obj):
        """Return public_score as score for API compatibility."""
        return obj.public_score


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Leaderboard entry serializer."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    
    class Meta:
        model = Leaderboard
        fields = [
            'rank', 'username', 'metric', 'best_score',
            'total_submissions', 'updated_at'
        ]
