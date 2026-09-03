from django.db import models
from django.conf import settings

CONCEPT_TAGS = [
    # Foundations
    ('python_ml', 'Python for ML'),
    ('numpy_pandas', 'NumPy & Pandas'),
    ('statistics', 'Statistics'),
    ('linear_algebra', 'Linear Algebra'),
    # Core ML
    ('regression', 'Regression'),
    ('classification', 'Classification'),
    ('evaluation_metrics', 'Evaluation Metrics'),
    ('feature_engineering', 'Feature Engineering'),
    ('gradient_descent', 'Gradient Descent'),
    ('regularization', 'Regularization'),
    # Advanced ML
    ('ensemble_learning', 'Ensemble Learning'),
    ('svm', 'SVM'),
    ('clustering', 'Clustering'),
    ('pca', 'PCA & Dimensionality Reduction'),
    # Deep Learning
    ('neural_networks', 'Neural Networks'),
    ('cnn', 'Convolutional Neural Networks'),
    ('rnn', 'Recurrent Neural Networks'),
    ('transformers', 'Transformers'),
    ('backpropagation', 'Backpropagation'),
    # MLOps
    ('model_deployment', 'Model Deployment'),
    ('mlops', 'MLOps'),
]


class ConceptMastery(models.Model):
    """Per-concept mastery score for a learner. Core of adaptive system."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='masteries')
    concept_tag = models.CharField(max_length=50, choices=CONCEPT_TAGS, db_index=True)

    # Component scores (0.0 to 1.0)
    quiz_mastery = models.FloatField(default=0.0)
    coding_mastery = models.FloatField(default=0.0)
    video_completion_rate = models.FloatField(default=0.0)

    # Computed composite score: weighted average
    mastery_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    bkt_trace = models.JSONField(default=list, blank=True)

    # Meta
    quiz_attempts = models.IntegerField(default=0)
    coding_attempts = models.IntegerField(default=0)
    is_struggling = models.BooleanField(default=False)  # True if mastery < 0.4 after 3+ attempts
    gap_detected = models.BooleanField(default=False)  # True if mastery < 0.4 and attempts >= 3
    last_updated = models.DateTimeField(auto_now=True)
    first_seen = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'concept_tag')
        indexes = [
            models.Index(fields=['user', 'mastery_score']),
            models.Index(fields=['user', 'concept_tag', 'mastery_score']),
            models.Index(fields=['user', 'gap_detected']),
        ]

    @property
    def is_knowledge_gap(self) -> bool:
        """Check if this concept is a knowledge gap."""
        return self.gap_detected

    def recompute_mastery(self):
        """Recompute mastery using local BKT; weighted formula when no response history."""
        from tracking.models import LearnerEvent
        from learner.bkt import BKTTracer, BKTParams, DEFAULT_PARAMS

        events = LearnerEvent.objects.filter(
            user=self.user,
            event_type__in=['QUIZ_PASSED', 'QUIZ_FAILED', 'CODE_PASSED', 'CODE_FAILED'],
            metadata__concept_tag=self.concept_tag,
        ).order_by('timestamp')
        history = [
            e.event_type in ('QUIZ_PASSED', 'CODE_PASSED')
            for e in events
        ]

        if not history:
            self.mastery_score = round(
                0.5 * self.quiz_mastery +
                0.35 * self.coding_mastery +
                0.15 * self.video_completion_rate,
                4,
            )
            self.is_struggling = (
                self.mastery_score < 0.4 and
                (self.quiz_attempts + self.coding_attempts) >= 3
            )
            self.gap_detected = self.is_struggling
            self.save(update_fields=['mastery_score', 'is_struggling', 'gap_detected', 'last_updated'])
            return

        params = DEFAULT_PARAMS.get(self.concept_tag, BKTParams())
        tracer = BKTTracer(params)
        p = params.p_init
        trace = [p]
        for correct in history:
            p = tracer.update(p, correct)
            trace.append(round(p, 4))

        self.mastery_score = round(p, 4)
        self.is_struggling = p < 0.4 and len(history) >= 3
        self.gap_detected = self.is_struggling
        self.bkt_trace = trace
        self.save(update_fields=['mastery_score', 'is_struggling', 'gap_detected', 'bkt_trace', 'last_updated'])

    def __str__(self):
        return f"{self.user.username} | {self.concept_tag} | {self.mastery_score:.2f}"


class LearnerProfile(models.Model):
    """Aggregated learner intelligence state. Updated async via Celery."""
    SKILL_LEVELS = [('beginner','Beginner'), ('intermediate','Intermediate'), ('advanced','Advanced')]
    CONTENT_PREFERENCES = [('video','Video'), ('quiz','Quiz'), ('coding','Coding'), ('mixed','Mixed')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learner_profile')

    # Estimated overall skill
    estimated_skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='beginner')
    overall_mastery = models.FloatField(default=0.0)  # average across all concepts

    # Engagement signals
    avg_session_duration_minutes = models.FloatField(default=0.0)
    total_sessions = models.IntegerField(default=0)
    total_lessons_completed = models.IntegerField(default=0)
    total_problems_solved = models.IntegerField(default=0)
    total_quizzes_passed = models.IntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)  # 0.0 to 1.0

    # Risk signals
    frustration_score = models.FloatField(default=0.0)  # high = many failures, low engagement
    dropout_risk = models.FloatField(default=0.0)        # 0.0 to 1.0
    learner_ability = models.FloatField(default=0.0)     # IRT theta estimate (~-3 to 3)
    streak_days = models.IntegerField(default=0)
    learning_velocity = models.FloatField(default=0.0)   # lessons completed per week (4-week rolling)

    # Preferences
    preferred_content_type = models.CharField(max_length=20, choices=CONTENT_PREFERENCES, default='mixed')
    preferred_difficulty = models.CharField(max_length=20, default='beginner')

    # Weak areas (list of concept_tags)
    weak_concepts = models.JSONField(default=list)
    strong_concepts = models.JSONField(default=list)

    last_active = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile: {self.user.username} | Skill: {self.estimated_skill_level} | Mastery: {self.overall_mastery:.2f}"


class LearningPath(models.Model):
    """Personalized ordered learning path for a user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_path')
    ordered_lesson_ids = models.JSONField(default=list)  # [lesson_id, ...]
    generated_at = models.DateTimeField(auto_now=True)
    is_adaptive = models.BooleanField(default=False)  # False = default, True = ML-generated

    def __str__(self):
        return f"Path: {self.user.username} | {len(self.ordered_lesson_ids)} lessons"