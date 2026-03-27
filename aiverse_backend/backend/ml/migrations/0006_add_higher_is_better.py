"""
Migration: Add higher_is_better field to Problem model.

CRITICAL: This migration:
1. Adds higher_is_better field with default=True
2. Backfills existing rows based on their metric type
3. Ensures higher_is_better is NEVER NULL going forward

After this migration, Problem.higher_is_better will:
- Be True for: accuracy, f1, precision, recall, r2, roc_auc
- Be False for: rmse, mae, mse
"""

from django.db import migrations, models


def backfill_higher_is_better(apps, schema_editor):
    """
    Backfill higher_is_better for all existing problems based on metric.
    
    Rules:
    - Lower is better metrics (rmse, mae, mse): higher_is_better = False
    - All other metrics: higher_is_better = True (default)
    """
    Problem = apps.get_model('ml', 'Problem')
    
    LOWER_IS_BETTER_METRICS = {'rmse', 'mae', 'mse'}
    
    # Update problems where metric is "lower is better"
    for problem in Problem.objects.all():
        # Get the active metric (prefer metric_type, fallback to metric)
        active_metric = (problem.metric_type or problem.metric or 'accuracy').lower().strip()
        
        if active_metric in LOWER_IS_BETTER_METRICS:
            problem.higher_is_better = False
        else:
            problem.higher_is_better = True
        
        problem.save(update_fields=['higher_is_better'])


def reverse_backfill(apps, schema_editor):
    """Reverse migration: set all to True (safe default)."""
    Problem = apps.get_model('ml', 'Problem')
    Problem.objects.all().update(higher_is_better=True)


class Migration(migrations.Migration):
    """Add higher_is_better field with proper backfill."""

    dependencies = [
        ('ml', '0005_upgrade_problem_system_phase1'),
    ]

    operations = [
        # Step 1: Add the field with default=True
        migrations.AddField(
            model_name='problem',
            name='higher_is_better',
            field=models.BooleanField(
                default=True,
                help_text='True if higher metric values are better (e.g., accuracy, f1). False for error metrics (e.g., rmse, mae).',
            ),
        ),
        
        # Step 2: Backfill existing rows based on their metric
        migrations.RunPython(
            backfill_higher_is_better,
            reverse_code=reverse_backfill,
        ),
    ]
