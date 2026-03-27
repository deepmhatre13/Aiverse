import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Override email to be unique & required
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)

    # Profile fields
    display_name = models.CharField(max_length=100, blank=True)
    tagline = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.CharField(max_length=160, blank=True)
    github_url = models.URLField(blank=True)
    github_username = models.CharField(max_length=39, blank=True)
    github_token = models.CharField(max_length=255, blank=True)
    
    linkedin_url = models.URLField(blank=True)
    linkedin_id = models.CharField(max_length=100, blank=True)
    linkedin_token = models.CharField(max_length=500, blank=True)
    
    website_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    skills = models.JSONField(default=list)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    # Score & ranking
    total_score = models.IntegerField(default=0)
    global_rank = models.IntegerField(null=True, blank=True)
    weekly_score = models.IntegerField(default=0)
    monthly_score = models.IntegerField(default=0)

    # Problem stats
    problems_solved = models.IntegerField(default=0)
    courses_completed = models.IntegerField(default=0)
    total_submissions = models.IntegerField(default=0)
    accepted_submissions = models.IntegerField(default=0)

    # Streak
    streak_days = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_submission_date = models.DateField(null=True, blank=True)

    # Entitlements & extras
    is_pro = models.BooleanField(default=False)
    badges = models.JSONField(default=list)
    preferences = models.JSONField(default=dict)

    # Auth method
    auth_method = models.CharField(
        max_length=20,
        choices=[('password', 'Email/Password'), ('google', 'Google OAuth')],
        default='password'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['-total_score']),
            models.Index(fields=['-weekly_score']),
            models.Index(fields=['-monthly_score']),
            models.Index(fields=['username']),
            models.Index(fields=['github_username']),
            models.Index(fields=['linkedin_id']),
        ]

    def __str__(self):
        return self.email

    @property
    def display(self):
        return self.display_name or self.username or self.email

    @property
    def success_rate(self):
        if self.total_submissions == 0:
            return 0.0
        return round((self.accepted_submissions / self.total_submissions) * 100, 2)


class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=240)
    tech_stack = models.JSONField(default=list)
    github_url = models.URLField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_projects'
        ordering = ['display_order', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'display_order']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"
