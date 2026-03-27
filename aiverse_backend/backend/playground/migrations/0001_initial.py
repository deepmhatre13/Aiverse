from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='playground/')),
                ('columns', models.JSONField(default=list)),
                ('target_column', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playground_datasets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'playground_datasets',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_step', models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4)])),
                ('task_type', models.CharField(blank=True, choices=[('classification', 'Classification'), ('regression', 'Regression')], max_length=20, null=True)),
                ('model_type', models.CharField(blank=True, max_length=64, null=True)),
                ('hyperparameters', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('CREATED', 'Created'), ('READY', 'Ready'), ('RUNNING', 'Running'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='CREATED', max_length=20)),
                ('score', models.FloatField(blank=True, null=True)),
                ('metrics', models.JSONField(default=dict)),
                ('error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='playground.dataset')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playground_experiments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'playground_experiments',
                'ordering': ['-created_at'],
            },
        ),
    ]
