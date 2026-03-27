from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Dataset(models.Model):
    """
    Preloaded dataset metadata only.
    Actual samples are loaded dynamically from sklearn during training.
    """
    TASK_CLASSIFICATION = 'classification'
    TASK_CHOICES = [(TASK_CLASSIFICATION, 'Classification')]

    name = models.CharField(max_length=64, unique=True, db_index=True)  # iris, breast_cancer, wine, digits
    task_type = models.CharField(max_length=32, choices=TASK_CHOICES, default=TASK_CLASSIFICATION)
    description = models.TextField(blank=True)
    n_samples = models.IntegerField(default=0)
    n_features = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playground_datasets'
        ordering = ['name']

    def __str__(self):
        return self.name


class Experiment(models.Model):
    STATUS_CREATED = 'CREATED'
    STATUS_READY = 'READY'
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Created'),
        (STATUS_READY, 'Ready'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='playground_experiments',
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='experiments',
    )
    current_step = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    model_type = models.CharField(max_length=64, null=True, blank=True)
    hyperparameters = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    metrics = models.JSONField(default=dict)
    logs = models.JSONField(default=list)  # free-form event logs (errors, warnings, timestamps)
    error = models.TextField(null=True, blank=True)  # traceback on failure
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'playground_experiments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Experiment {self.pk} ({self.status})"


class TrainingLog(models.Model):
    """Per-epoch metrics persisted for UI streaming + history."""
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name='training_logs',
    )
    epoch = models.IntegerField()
    loss = models.FloatField()
    accuracy = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playground_training_logs'
        ordering = ['epoch']
        indexes = [
            models.Index(fields=['experiment', 'epoch']),
        ]
