import uuid
from django.db import models


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'), ('Medium', 'Medium'),
        ('Hard', 'Hard'), ('Expert', 'Expert'),
    ]
    CATEGORY_CHOICES = [
        ('Classification', 'Classification'),
        ('Regression', 'Regression'),
        ('NLP', 'NLP'),
        ('Computer Vision', 'Computer Vision'),
        ('Reinforcement Learning', 'Reinforcement Learning'),
        ('Statistics', 'Statistics'),
        ('Time Series', 'Time Series'),
        ('Clustering', 'Clustering'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='Medium')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    points = models.IntegerField(default=100)
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField(blank=True)
    test_cases = models.JSONField(default=list)
    hints = models.JSONField(default=list)
    tags = models.JSONField(default=list)
    constraints = models.TextField(blank=True)
    examples = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    solve_count = models.IntegerField(default=0)
    attempt_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    order_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'problems'
        ordering = ['order_index', 'difficulty']
        indexes = [
            models.Index(fields=['difficulty']),
            models.Index(fields=['category']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.title} [{self.difficulty}]'
