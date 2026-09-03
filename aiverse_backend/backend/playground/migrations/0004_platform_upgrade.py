# Generated manually for platform upgrade

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playground', '0003_seed_preloaded_datasets'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='algorithm',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='experiment',
            name='concept_tag',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='experiment',
            name='dataset_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='experiment',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='experiment',
            name='preprocessing_config',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='experiment',
            name='results',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='experiment',
            name='run_time_seconds',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='experiment',
            name='tags',
            field=models.JSONField(default=list),
        ),
        migrations.AddIndex(
            model_name='experiment',
            index=models.Index(fields=['user', '-created_at'], name='playground__user_id_created_idx'),
        ),
    ]
