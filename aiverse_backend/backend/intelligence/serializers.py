from rest_framework import serializers

from intelligence.models import ExperimentRun, SuggestionLog, UserActivity, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "skill_level",
            "avg_score",
            "total_runs",
            "strengths",
            "weaknesses",
            "preferred_models",
            "last_active",
        ]


class SuggestionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestionLog
        fields = ["suggestion_type", "message", "context", "created_at"]


class ExperimentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentRun
        fields = [
            "id",
            "dataset_name",
            "model_type",
            "hyperparameters",
            "accuracy",
            "loss",
            "task_type",
            "created_at",
        ]


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ["id", "activity_type", "reference_id", "metadata", "created_at"]
