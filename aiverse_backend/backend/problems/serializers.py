from rest_framework import serializers
from .models import Problem


class ProblemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'slug', 'difficulty', 'category', 'points',
            'short_description', 'tags', 'solve_count', 'attempt_count',
            'is_active', 'order_index', 'created_at',
        ]


class ProblemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'difficulty', 'category', 'points',
            'starter_code', 'hints', 'tags', 'constraints', 'examples',
            'solve_count', 'attempt_count', 'created_at', 'updated_at',
        ]
        # Never expose solution_code or full test_cases to client
