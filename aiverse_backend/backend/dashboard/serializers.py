from rest_framework import serializers
from .models import UserActivity
from ml.models import Submission


class PerformanceRecentSubmissionSerializer(serializers.Serializer):
    id = serializers.CharField()
    problem_name = serializers.CharField()
    status = serializers.CharField()
    score = serializers.FloatField()
    created_at = serializers.DateTimeField()


class PerformanceResponseSerializer(serializers.Serializer):
    total_score = serializers.FloatField()
    problems_solved = serializers.IntegerField()
    submissions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    current_streak = serializers.IntegerField()
    global_rank = serializers.IntegerField(allow_null=True, required=False)
    recent_submissions = PerformanceRecentSubmissionSerializer(many=True)


class UserActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'activity_type_display', 'created_at']
        read_only_fields = ['id', 'created_at']


class DashboardOverviewSerializer(serializers.Serializer):
    total_problems_attempted = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    videos_watched = serializers.IntegerField()
    courses_purchased = serializers.IntegerField()
    mentor_sessions_used = serializers.IntegerField()


class SubmissionHistorySerializer(serializers.ModelSerializer):
    problem_name = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    submitted_at = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id',
            'problem_name',
            'problem_slug',
            'status',
            'score',
            'submitted_at',
        ]
        read_only_fields = fields