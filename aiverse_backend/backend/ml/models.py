from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User=get_user_model()


class Dataset(models.Model):
    """
    First-class Dataset entity for ML problems.
    
    CRITICAL: Every Problem MUST reference a Dataset.
    Datasets are reusable across multiple problems.
    
    Loader Types:
        - sklearn: Built-in sklearn datasets (iris, breast_cancer, digits, wine)
        - csv: CSV file on disk
        - url: Remote URL (S3, HTTP)
        - registry: Defined in ml/registry.py (for registry-based problems)
    """
    
    LOADER_TYPE_CHOICES = [
        ('sklearn', 'scikit-learn built-in'),
        ('csv', 'CSV file'),
        ('url', 'Remote URL'),
        ('registry', 'Registry-defined'),
    ]
    
    name = models.CharField(
        max_length=255,
        help_text="Human-readable dataset name"
    )
    slug = models.SlugField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text="URL-safe identifier (auto-generated from name)"
    )
    description = models.TextField(
        blank=True,
        help_text="Dataset description and usage notes"
    )
    
    loader_type = models.CharField(
        max_length=20,
        choices=LOADER_TYPE_CHOICES,
        default='registry',
        help_text="How to load this dataset"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path or identifier: sklearn name, file path, or URL"
    )
    target_column = models.CharField(
        max_length=100,
        blank=True,
        help_text="Target column name (for CSV datasets)"
    )
    
    # Dataset metadata
    num_samples = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of samples in dataset"
    )
    num_features = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of features"
    )
    task_type = models.CharField(
        max_length=20,
        choices=[('classification', 'Classification'), ('regression', 'Regression')],
        default='classification',
        help_text="ML task type"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ml_datasets'
        ordering = ['name']
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
    
    def __str__(self):
        return f"{self.name} ({self.loader_type})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DatasetConfig(models.Model):
    """
    Encapsulates where a dataset comes from and how it's loaded.
    
    CRITICAL: This is the ONLY place datasets are defined.
    This separation ensures dataset loading is independent of problem definition.
    
    Examples:
        1. Iris via sklearn:
           - loader_type = 'sklearn'
           - dataset_identifier = 'iris'
           - target_column = 'species' (ignored for sklearn, used for CSV)
           - test_size = 0.2
           - random_state = 42
        
        2. CSV file:
           - loader_type = 'csv'
           - dataset_identifier = 'data/cancer.csv'
           - target_column = 'diagnosis'
           - test_size = 0.2
           - random_state = 42
    """
    
    LOADER_CHOICES = [
        ('sklearn', 'scikit-learn built-in dataset'),
        ('csv', 'CSV file on disk'),
    ]
    
    problem = models.OneToOneField(
        'Problem',
        on_delete=models.CASCADE,
        related_name='dataset_config'
    )
    
    loader_type = models.CharField(
        max_length=20,
        choices=LOADER_CHOICES,
        help_text="Type of data loader: sklearn built-in or CSV file"
    )
    
    dataset_identifier = models.CharField(
        max_length=255,
        help_text="For sklearn: 'iris', 'breast_cancer', 'digits', 'wine'. For CSV: path to file."
    )
    
    test_size = models.FloatField(
        default=0.2,
        help_text="Fraction of data for testing (0.0-1.0)"
    )
    
    random_state = models.IntegerField(
        default=42,
        help_text="Random seed for reproducible train/test split"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ml_datasetconfigs'
        verbose_name = 'Dataset Configuration'
        verbose_name_plural = 'Dataset Configurations'
    
    def __str__(self):
        return f"DatasetConfig for {self.problem.title} ({self.loader_type})"
    
    def load(self):
        """
        Load and split dataset.
        
        DEPRECATED: DatasetConfig is no longer used in the new registry-based system.
        All datasets are now defined in ml/registry.py with inline loaders.
        
        This method is kept for backward compatibility but will raise an error.
        """
        raise NotImplementedError(
            "DatasetConfig.load() is deprecated. "
            "Use ml.registry.get_problem_definition(slug).load_visible_dataset() instead."
        )


class Problem(models.Model):
    """
    Industrial-grade ML problem definition.
    
    Each problem includes:
    - Difficulty rating (800, 1200, 1600, 2000)
    - Dataset metadata (shape, features, target info)
    - Metric configuration
    - Performance thresholds
    - Resource constraints (latency, memory)
    - Hidden evaluation dataset location
    - Industrial constraints
    """
    
    PROBLEM_TYPE_CHOICES=[
        ('classification','Classification'),
        ('regression','Regression'),
    ]

    METRIC_CHOICES=[
        ('accuracy','Accuracy'),
        ('f1','F1 Score'),
        ('rmse','RMSE'),
        ('mae','Mean Absolute Error'),
        ('r2','R² Score'),
        ('precision','Precision'),
        ('recall','Recall'),
        ('roc_auc','ROC AUC'),
    ]

    DIFFICULTY_RATING_CHOICES=[
        (800, 'Easy (800)'),
        (1200, 'Medium (1200)'),
        (1600, 'Hard (1600)'),
        (2000, 'Expert (2000)'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]

    title=models.CharField(max_length=255)
    slug=models.SlugField(unique=True,max_length=255,db_index=True)
    short_description=models.CharField(max_length=255, blank=True, null=True, help_text="Brief 1-2 sentence summary")
    description=models.TextField(blank=True, null=True, help_text="Full problem description (supports markdown)")
    problem_type=models.CharField(max_length=20,choices=PROBLEM_TYPE_CHOICES)
    
    # Dataset reference (REQUIRED for all problems)
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name='problems',
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="Dataset used for this problem. REQUIRED for submissions."
    )
    
    # Difficulty field (VARCHAR for human-readable difficulty)
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        help_text="Problem difficulty: easy, medium, hard, expert"
    )
    
    # Industrial-grade fields
    difficulty_rating=models.IntegerField(
        choices=DIFFICULTY_RATING_CHOICES,
        default=800,
        help_text="Problem difficulty rating (800=Easy, 1200=Medium, 1600=Hard, 2000=Expert)"
    )
    
    dataset_metadata=models.JSONField(
        default=dict,
        blank=True,
        help_text="Dataset metadata: shape, features, target distribution, etc."
    )
    
    metric_type=models.CharField(
        max_length=50,
        choices=METRIC_CHOICES,
        default='accuracy',
        help_text="Primary metric for evaluation"
    )
    
    # Legacy metric field (kept for backward compatibility)
    metric=models.CharField(max_length=20,choices=METRIC_CHOICES, blank=True, default='accuracy')
    
    threshold=models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum score threshold for acceptance (null = no threshold)"
    )
    
    higher_is_better=models.BooleanField(
        default=True,
        help_text="True if higher metric values are better (e.g., accuracy, f1). False for error metrics (e.g., rmse, mae)."
    )
    
    latency_limit_ms=models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum allowed inference latency in milliseconds (null = no limit)"
    )
    
    memory_limit_mb=models.IntegerField(
        default=512,
        help_text="Maximum allowed memory usage in MB (default: 512)"
    )
    
    time_limit_seconds=models.IntegerField(
        default=30,
        help_text="Maximum allowed execution time in seconds (default: 30)"
    )
    
    hidden_dataset_location=models.CharField(
        max_length=500,
        blank=True,
        help_text="S3 path or secure location for hidden evaluation dataset"
    )
    
    evaluation_config=models.JSONField(
        default=dict,
        blank=True,
        help_text="Evaluation configuration: test splits, cross-validation settings, etc."
    )
    
    industrial_constraints=models.TextField(
        blank=True,
        help_text="Industrial constraints and requirements (e.g., 'Model must be < 10MB', 'Latency < 100ms')"
    )
    
    is_competition_problem=models.BooleanField(
        default=False,
        help_text="True if this problem is part of a competition"
    )
    
    # Legacy fields (kept for backward compatibility)
    target_column=models.CharField(max_length=100, blank=True)
    dataset_dir=models.CharField(max_length=500, blank=True)
    
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        db_table='ml_problems'
        ordering=['difficulty_rating', 'created_at']
        indexes=[
            models.Index(fields=['difficulty_rating', 'is_active']),
            models.Index(fields=['is_competition_problem', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} ({self.difficulty_rating})"
    
    # Metrics where LOWER is better
    LOWER_IS_BETTER = {'rmse', 'mae', 'mse'}
    # Metrics where HIGHER is better
    HIGHER_IS_BETTER = {'accuracy', 'f1', 'precision', 'recall', 'r2', 'roc_auc'}
    
    def save(self,*args,**kwargs):
        if not self.slug:
            self.slug=slugify(self.title)
        
        # DEFENSIVE: Ensure difficulty is NEVER null
        if not self.difficulty:
            self.difficulty = 'medium'
        
        # Sync difficulty_rating with difficulty for consistency
        difficulty_to_rating = {
            'easy': 800,
            'medium': 1200,
            'hard': 1600,
            'expert': 2000,
        }
        if self.difficulty in difficulty_to_rating and not self.difficulty_rating:
            self.difficulty_rating = difficulty_to_rating[self.difficulty]
        
        # Sync metric_type to metric for backward compatibility
        if not self.metric and self.metric_type:
            self.metric = self.metric_type
        
        # Auto-set higher_is_better based on metric (NEVER allow NULL)
        # Use metric_type (primary) or metric (backward compatibility)
        active_metric = (self.metric_type or self.metric or 'accuracy').lower().strip()
        if active_metric in self.LOWER_IS_BETTER:
            self.higher_is_better = False
        else:
            # Default to True for accuracy, f1, etc.
            self.higher_is_better = True
        
        super().save(*args,**kwargs)

class TestSuite(models.Model):
    """
    Test suite for a problem.
    
    Each problem MUST have exactly one test suite.
    Test suite contains BOTH public and private tests.
    
    Tests are stored as JSON for database portability:
    [
        {
            "name": str,
            "metric": "accuracy" | "f1" | "rmse" | "mae" | "r2",
            "threshold": float,
            "X_train_shape": [int, int],
            "X_test_shape": [int, int],
            "y_train_shape": [int] | [int, int],
            "y_test_shape": [int] | [int, int],
            ... (serialized test case data)
        }
    ]
    """
    
    problem=models.OneToOneField(
        Problem,
        on_delete=models.CASCADE,
        related_name='testsuite'
    )
    
    public_tests=models.JSONField(
        default=list,
        blank=True,
        help_text="Dataset splits for public evaluation"
    )
    
    private_tests=models.JSONField(
        default=list,
        blank=True,
        help_text="Dataset splits for private submission evaluation"
    )
    
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table='ml_testsuites'
        verbose_name='Test Suite'
        verbose_name_plural='Test Suites'
    
    def __str__(self):
        return f"TestSuite for {self.problem.title}"


class Submission(models.Model):
    """
    IMMUTABLE submission record - one row per submission.
    
    CRITICAL INVARIANTS:
    ✓ Each submission is a NEW row (never updated, never overwritten)
    ✓ Submission history is complete and permanent
    ✓ Code snapshot is preserved exactly as submitted
    ✓ No unique_together constraint (allows multiple submissions per user/problem)
    ✓ Status is ACCEPTED | REJECTED | ERROR (not passed/failed)
    
    Submission lifecycle:
    1. User evaluates code (stateless, no DB write)
    2. User submits code (creates new Submission row)
    3. Server evaluates, checks threshold, measures latency/memory
    4. If threshold met: status=ACCEPTED, rank calculated
    5. If threshold not met: status=REJECTED, reason stored
    6. If error: status=ERROR, error_log stored
    7. Row is NEVER updated after creation
    """
    
    STATUS_CHOICES = [
        ('ACCEPTED', 'Accepted'),       # Submission met threshold (terminal)
        ('REJECTED', 'Rejected'),       # Submission below threshold (terminal)
        ('ERROR', 'Error'),             # Evaluation error (terminal)
    ]

    VERDICT_CHOICES = [
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    # Primary data: what was submitted
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.PROTECT,
        related_name='submissions',
        null=True,  # Nullable for backward compatibility
        blank=True,
        help_text="Dataset used for this submission (copied from problem at submission time)"
    )
    code = models.TextField(help_text="Full code snapshot as submitted by user")
    
    # Evaluation results
    metric = models.CharField(
        max_length=50,
        help_text="Metric used for evaluation (accuracy, f1, rmse, etc)"
    )
    score = models.FloatField(
        default=0.0,
        help_text="Score on metric (0.0-1.0 for accuracy, varies for others)"
    )
    threshold = models.FloatField(
        null=True,
        blank=True,
        help_text="Submission threshold value at time of submission"
    )
    
    # Performance metrics
    latency_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Inference latency in milliseconds"
    )
    memory_mb = models.FloatField(
        null=True,
        blank=True,
        help_text="Memory usage in megabytes"
    )
    meets_threshold = models.BooleanField(
        default=False,
        help_text="Whether submission meets the threshold requirement"
    )
    verdict = models.CharField(
        max_length=20,
        choices=VERDICT_CHOICES,
        null=True,
        blank=True,
        help_text="Final verdict: ACCEPTED or REJECTED"
    )
    
    # Status and ranking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="ACCEPTED=meets threshold, REJECTED=below threshold, ERROR=eval error"
    )
    rank = models.IntegerField(
        null=True,
        blank=True,
        help_text="Leaderboard rank (only for ACCEPTED submissions)"
    )
    
    # Evaluation metadata
    evaluation_version = models.CharField(
        max_length=50,
        default='1.0.0',
        help_text="Version of evaluation engine used (for reproducibility)"
    )
    model_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Model metadata: type, hyperparameters, feature count, etc."
    )
    
    # Diagnostics
    error_log = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if status=ERROR"
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for rejection if status=REJECTED (e.g., 'Score 0.63 below threshold 0.80')"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    runtime_seconds = models.FloatField(null=True, blank=True)
    test_results = models.JSONField(
        default=list,
        blank=True,
        help_text="Detailed evaluation results (optional)"
    )

    class Meta:
        db_table = 'ml_submissions'
        ordering = ['-created_at']
        indexes = [
            # Allow fast lookups: "get all submissions for user/problem"
            models.Index(fields=['user', 'problem', '-created_at']),
            # Allow fast leaderboard queries: "rank submissions by score for problem"
            models.Index(fields=['problem', 'status', '-score', 'latency_ms']),
            # Allow fast recent submissions: "get recent submissions for problem"
            models.Index(fields=['problem', '-created_at']),
            # Leaderboard sorting: score DESC, latency ASC, timestamp ASC
            models.Index(fields=['problem', 'status', '-score', 'latency_ms', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}→{self.problem.slug}@{self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """PRODUCTION SAFETY: Never allow updates to existing submission."""
        if self.pk:
            # Submission already exists - prevent all updates
            raise ValueError(
                "Submissions are immutable. Create a new submission instead of updating."
            )
        # Set verdict based on status
        if self.status == 'ACCEPTED':
            self.verdict = 'ACCEPTED'
        elif self.status == 'REJECTED':
            self.verdict = 'REJECTED'
        super().save(*args, **kwargs)