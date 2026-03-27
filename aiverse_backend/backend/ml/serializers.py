from rest_framework import serializers
from .models import Problem, Submission, Dataset


# Metric direction constants
HIGHER_IS_BETTER_METRICS = {'accuracy', 'f1', 'precision', 'recall', 'r2', 'roc_auc'}
LOWER_IS_BETTER_METRICS = {'rmse', 'mae', 'mse'}


def compute_higher_is_better(metric: str) -> bool:
    """Determine if higher values are better for a given metric."""
    metric_lower = (metric or 'accuracy').lower().strip()
    return metric_lower not in LOWER_IS_BETTER_METRICS


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for Dataset model."""
    
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'loader_type',
            'file_path',
            'target_column',
            'num_samples',
            'num_features',
            'task_type',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DatasetMinimalSerializer(serializers.ModelSerializer):
    """Minimal dataset info for embedding in problem responses."""
    
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'slug', 'loader_type', 'task_type']


class ProblemListSerializer(serializers.ModelSerializer):
    """Serializer for listing problems."""
    higher_is_better = serializers.SerializerMethodField()
    
    class Meta:
        model = Problem
        fields = [
            'id',
            'title',
            'slug',
            'problem_type',
            'metric',
            'difficulty',
            'difficulty_rating',
            'higher_is_better',
            'is_active',
            'created_at',
        ]
    
    def get_higher_is_better(self, obj):
        return getattr(obj, 'higher_is_better', compute_higher_is_better(obj.metric))


class ProblemDetailSerializer(serializers.ModelSerializer):
    """Serializer for problem detail with full description."""
    higher_is_better = serializers.SerializerMethodField()
    short_description = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = Problem
        fields = [
            'id',
            'title',
            'slug',
            'short_description',
            'description',
            'problem_type',
            'metric',
            'difficulty',
            'difficulty_rating',
            'higher_is_better',
            'target_column',
            'dataset_dir',
            'memory_limit_mb',
            'time_limit_seconds',
            'latency_limit_ms',
            'is_active',
            'created_at',
        ]
    
    def get_higher_is_better(self, obj):
        return getattr(obj, 'higher_is_better', compute_higher_is_better(obj.metric))


class ProblemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating problems with automatic higher_is_better calculation."""
    
    dataset = serializers.PrimaryKeyRelatedField(
        queryset=Dataset.objects.all(),
        required=True,
        help_text="Dataset ID (required). Every problem MUST have a dataset."
    )
    
    difficulty = serializers.CharField(
        required=False,
        default='medium',
        help_text="Problem difficulty: easy, medium, hard, expert"
    )
    
    class Meta:
        model = Problem
        fields = [
            'title',
            'description',
            'problem_type',
            'metric_type',
            'threshold',
            'dataset',
            'difficulty',
        ]
    
    def validate_difficulty(self, value):
        """Ensure difficulty is never null and has valid value."""
        if value is None or value == '':
            return 'medium'
        valid_difficulties = {'easy', 'medium', 'hard', 'expert'}
        if value.lower() not in valid_difficulties:
            return 'medium'
        return value.lower()
    
    def validate(self, data):
        """Ensure metric has valid type and dataset is assigned."""
        # Validate metric
        metric = data.get('metric_type') or data.get('metric', 'accuracy')
        metric_lower = metric.lower().strip()
        
        known_metrics = HIGHER_IS_BETTER_METRICS | LOWER_IS_BETTER_METRICS
        if metric_lower not in known_metrics:
            raise serializers.ValidationError({
                'metric_type': f"Unknown metric '{metric}'. Supported: {', '.join(sorted(known_metrics))}"
            })
        
        # Validate dataset is assigned (REQUIRED, not optional)
        if not data.get('dataset'):
            raise serializers.ValidationError({
                'dataset': "Dataset must be assigned. Every problem requires a dataset."
            })
        
        # Ensure difficulty has default
        if not data.get('difficulty'):
            data['difficulty'] = 'medium'
        
        return data


class SubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a submission (evaluate or submit)."""
    
    code = serializers.CharField()
    
    def validate_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Code cannot be empty")
        
        # Basic validation: must contain the required function
        if 'def train_and_predict' not in value:
            raise serializers.ValidationError(
                "Code must define: def train_and_predict(X_train, y_train, X_test)"
            )
        
        return value


class ProblemMiniSerializer(serializers.ModelSerializer):
    """Lightweight nested serializer for submissions."""
    class Meta:
        model = Problem
        fields = ["id", "title", "slug", "difficulty"]


class SubmissionListSerializer(serializers.ModelSerializer):
    """Serializer for listing submissions with nested problem."""
    problem = ProblemMiniSerializer(read_only=True)
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id',
            'problem',
            'problem_title',
            'problem_slug',
            'status',
            'score',
            'metric',
            'rank',
            'latency_ms',
            'memory_mb',
            'meets_threshold',
            'verdict',
            'created_at',
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed submission view (includes full code snapshot)."""
    
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id',
            'user_username',
            'problem_title',
            'problem_slug',
            'code',               # ✅ CRITICAL: Full code snapshot
            'status',
            'score',
            'metric',
            'threshold',
            'rank',
            'latency_ms',
            'memory_mb',
            'meets_threshold',
            'verdict',
            'reason',
            'error_log',
            'runtime_seconds',
            'test_results',
            'evaluation_version',
            'model_metadata',
            'created_at',
        ]