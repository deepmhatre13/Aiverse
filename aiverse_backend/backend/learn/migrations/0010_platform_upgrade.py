# Generated manually for platform upgrade

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('learn', '0009_module_lesson_concept_tag_lesson_difficulty_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='course',
            name='concept_tag',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AddField(
            model_name='course',
            name='module',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses', to='learn.module',
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='slug',
            field=models.SlugField(blank=True, db_index=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='category',
            field=models.CharField(default='Fundamentals', max_length=50),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='metric',
            field=models.CharField(default='ACCURACY', max_length=50),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='points',
            field=models.IntegerField(default=800),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='starter_code',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='test_cases',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='expected_output_format',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='constraints',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='hints',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='tags',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='solve_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='avg_attempts',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='codingproblem',
            name='concept_tag',
            field=models.CharField(db_index=True, default='classification', max_length=50),
        ),
        migrations.AlterField(
            model_name='codingproblem',
            name='difficulty',
            field=models.CharField(
                choices=[
                    ('easy', 'Easy'), ('medium', 'Medium'),
                    ('hard', 'Hard'), ('expert', 'Expert'),
                ],
                default='easy', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='codingproblem',
            name='related_lessons',
            field=models.ManyToManyField(blank=True, related_name='related_problems', to='learn.lesson'),
        ),
        migrations.AlterModelOptions(
            name='codingproblem',
            options={'ordering': ['order', 'difficulty']},
        ),
    ]
