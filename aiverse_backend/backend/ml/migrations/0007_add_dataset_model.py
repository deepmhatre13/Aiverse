# Generated migration for adding Dataset model
# This migration:
# 1. Creates the Dataset table
# 2. Adds dataset FK to Problem IF NOT EXISTS (nullable temporarily)
# 3. Creates default "registry_default" dataset
# 4. Backfills existing problems with the default dataset
# 5. Adds dataset FK to Submission IF NOT EXISTS (nullable for backward compatibility)

from django.db import migrations, models, connection
import django.db.models.deletion


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, [table_name, column_name])
        return cursor.fetchone()[0] > 0


def create_default_dataset(apps, schema_editor):
    """
    Create a default dataset for registry-based problems.
    All existing problems will be assigned to this dataset.
    """
    Dataset = apps.get_model('ml', 'Dataset')
    
    # Create the default registry dataset
    default_dataset, created = Dataset.objects.get_or_create(
        slug='registry-default',
        defaults={
            'name': 'Registry Default Dataset',
            'description': 'Default dataset for registry-based problems. '
                           'These problems load data from inline loaders defined in ml/registry.py.',
            'loader_type': 'registry',
            'file_path': '',
            'target_column': '',
            'task_type': 'classification',
        }
    )
    
    # Backfill all existing problems with the default dataset
    Problem = apps.get_model('ml', 'Problem')
    Problem.objects.filter(dataset__isnull=True).update(dataset=default_dataset)


def reverse_default_dataset(apps, schema_editor):
    """
    Reverse migration: set all problem.dataset to NULL.
    """
    Problem = apps.get_model('ml', 'Problem')
    Problem.objects.all().update(dataset=None)


class AddFieldIfNotExists(migrations.AddField):
    """Custom AddField that skips if column already exists."""
    
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # Get the actual column name (for ForeignKey it's field_name + '_id')
        model = to_state.apps.get_model(app_label, self.model_name)
        table_name = model._meta.db_table
        
        # For ForeignKey, the column name is field_name + '_id'
        col_name = self.name + '_id' if hasattr(self.field, 'remote_field') and self.field.remote_field else self.name
        
        if not column_exists(table_name, col_name):
            super().database_forwards(app_label, schema_editor, from_state, to_state)
    
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        model = from_state.apps.get_model(app_label, self.model_name)
        table_name = model._meta.db_table
        col_name = self.name + '_id' if hasattr(self.field, 'remote_field') and self.field.remote_field else self.name
        
        if column_exists(table_name, col_name):
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('ml', '0006_add_higher_is_better'),
    ]

    operations = [
        # Step 1: Create Dataset table
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Human-readable dataset name', max_length=255)),
                ('slug', models.SlugField(db_index=True, help_text='URL-safe identifier (auto-generated from name)', max_length=255, unique=True)),
                ('description', models.TextField(blank=True, help_text='Dataset description and usage notes')),
                ('loader_type', models.CharField(choices=[('sklearn', 'scikit-learn built-in'), ('csv', 'CSV file'), ('url', 'Remote URL'), ('registry', 'Registry-defined')], default='registry', help_text='How to load this dataset', max_length=20)),
                ('file_path', models.CharField(blank=True, help_text='Path or identifier: sklearn name, file path, or URL', max_length=500)),
                ('target_column', models.CharField(blank=True, help_text='Target column name (for CSV datasets)', max_length=100)),
                ('num_samples', models.IntegerField(blank=True, help_text='Number of samples in dataset', null=True)),
                ('num_features', models.IntegerField(blank=True, help_text='Number of features', null=True)),
                ('task_type', models.CharField(choices=[('classification', 'Classification'), ('regression', 'Regression')], default='classification', help_text='ML task type', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Dataset',
                'verbose_name_plural': 'Datasets',
                'db_table': 'ml_datasets',
                'ordering': ['name'],
            },
        ),
        
        # Step 2: Add dataset FK to Problem IF NOT EXISTS (nullable at first)
        AddFieldIfNotExists(
            model_name='problem',
            name='dataset',
            field=models.ForeignKey(
                blank=True,
                help_text='Dataset used for this problem. REQUIRED for submissions.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='problems',
                to='ml.dataset',
            ),
        ),
        
        # Step 3: Add dataset FK to Submission IF NOT EXISTS (nullable for backward compatibility)
        AddFieldIfNotExists(
            model_name='submission',
            name='dataset',
            field=models.ForeignKey(
                blank=True,
                help_text='Dataset used for this submission (copied from problem at submission time)',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='submissions',
                to='ml.dataset',
            ),
        ),
        
        # Step 4: Create default dataset and backfill existing problems
        migrations.RunPython(
            create_default_dataset,
            reverse_default_dataset,
        ),
    ]