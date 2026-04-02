from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    SKILL_BEGINNER = "beginner"
    SKILL_INTERMEDIATE = "intermediate"
    SKILL_ADVANCED = "advanced"
    SKILL_CHOICES = [
        (SKILL_BEGINNER, "Beginner"),
        (SKILL_INTERMEDIATE, "Intermediate"),
        (SKILL_ADVANCED, "Advanced"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intelligence_profile")
    skill_level = models.CharField(max_length=32, choices=SKILL_CHOICES, default=SKILL_BEGINNER)
    avg_score = models.FloatField(default=0.0)
    total_runs = models.IntegerField(default=0)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    preferred_models = models.JSONField(default=list, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "intelligence_user_profile"
        indexes = [models.Index(fields=["skill_level"]), models.Index(fields=["-last_active"])]

    def touch(self):
        self.last_active = timezone.now()
        self.save(update_fields=["last_active"])


class UserActivity(models.Model):
    TYPE_PROBLEM = "problem"
    TYPE_PLAYGROUND = "playground"
    TYPE_MENTOR = "mentor"
    TYPE_LEARN = "learn"
    TYPE_CHOICES = [
        (TYPE_PROBLEM, "Problem"),
        (TYPE_PLAYGROUND, "Playground"),
        (TYPE_MENTOR, "Mentor"),
        (TYPE_LEARN, "Learn"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intelligence_activities")
    activity_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    reference_id = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intelligence_user_activity"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "activity_type", "-created_at"]),
        ]


class ExperimentRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intelligence_experiment_runs")
    dataset_name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=128)
    hyperparameters = models.JSONField(default=dict, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    task_type = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intelligence_experiment_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "model_type"]),
            models.Index(fields=["user", "dataset_name"]),
        ]


class SuggestionLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="intelligence_suggestions")
    suggestion_type = models.CharField(max_length=64)
    message = models.TextField()
    context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intelligence_suggestion_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "suggestion_type", "-created_at"]),
        ]

