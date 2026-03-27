from rest_framework import serializers
from .models import Submission
from problems.serializers import ProblemListSerializer


class SubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    problem_difficulty = serializers.CharField(source='problem.difficulty', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'problem', 'problem_title', 'problem_slug', 'problem_difficulty',
            'language', 'status', 'score', 'max_score',
            'execution_time_ms', 'memory_mb',
            'test_results', 'error_message', 'submitted_at', 'is_best',
        ]
        read_only_fields = [
            'id', 'status', 'score', 'max_score', 'execution_time_ms',
            'memory_mb', 'test_results', 'error_message', 'submitted_at', 'is_best',
        ]


class SubmitSerializer(serializers.Serializer):
    problem_slug = serializers.SlugField()
    code = serializers.CharField()
    language = serializers.ChoiceField(choices=['python', 'r'], default='python')


class RunSerializer(serializers.Serializer):
    problem_slug = serializers.SlugField()
    code = serializers.CharField()
    language = serializers.ChoiceField(choices=['python', 'r'], default='python')
