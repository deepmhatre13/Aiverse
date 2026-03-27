"""
ML Problem and Submission models.
Supports metric-based evaluation (not test-case-based).
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Problem(models.Model):
    """ML coding problem definition."""
    
    TASK_CHOICES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
    ]
    
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_CHOICES)
    
    # Metrics configuration
    default_metric = models.CharField(max_length=50)
    allowed_metrics = models.JSONField(default=list)  # e.g., ["accuracy", "f1", "precision"]
    
    # Submission threshold (minimum score to accept)
    submission_threshold = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Starter code template for this problem
    starter_code = models.TextField(
        default="""def train_and_predict(X_train, y_train, X_test):
    # TODO: Implement your solution
    pass
"""
    )
    
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.slug})"


class Submission(models.Model):
    """User's code submission with evaluation results."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),          # User is editing
        ('evaluated', 'Evaluated'),   # Evaluation complete (not submitted)
        ('passed', 'Passed'),         # Final submission accepted
        ('rejected', 'Rejected'),     # Below threshold
        ('error', 'Error'),           # Evaluation error
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ml_submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    
    code = models.TextField()
    metric = models.CharField(max_length=50)
    
    # Results (using public_score for leaderboard visibility)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    public_score = models.FloatField(null=True, blank=True)  # Visible in leaderboard
    private_score = models.FloatField(null=True, blank=True) # Hidden validation score (same for now)
    
    # Error handling
    error_type = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Leaderboard
    rank = models.IntegerField(null=True, blank=True)
    is_best = models.BooleanField(default=False)  # Best score for this user on this problem
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = []  # Allow multiple submissions per user per problem
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.slug} ({self.status})"


class Leaderboard(models.Model):
    """Leaderboard entry (best score per user per problem)."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='leaderboard')
    
    best_submission = models.ForeignKey(
        Submission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leaderboard_entry'
    )
    
    metric = models.CharField(max_length=50)
    best_score = models.FloatField()
    rank = models.IntegerField()
    
    # Stats
    total_submissions = models.IntegerField(default=1)
    total_attempts = models.IntegerField(default=1)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['problem', '-best_score', 'rank']
        unique_together = [['user', 'problem']]
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.slug} (Rank: {self.rank})"
