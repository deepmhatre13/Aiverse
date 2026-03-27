"""
Management command to populate DatasetConfig records for all problems.

DatasetConfig specifies WHERE each problem's data comes from:
- loader_type: 'sklearn' (built-in) or 'csv' (file on disk)
- dataset_identifier: name or path
- test_size: fraction for testing
- random_state: reproducibility seed

Usage:
    python manage.py populate_dataset_configs
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ml.models import Problem, DatasetConfig


class Command(BaseCommand):
    help = 'Populate DatasetConfig records for all ML problems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Define DatasetConfig for each problem
        configs = [
            {
                'problem_slug': 'iris-species-classification',
                'loader_type': 'sklearn',
                'dataset_identifier': 'iris',
                'test_size': 0.2,
                'random_state': 42,
            },
            {
                'problem_slug': 'spam-detection',
                'loader_type': 'sklearn',
                'dataset_identifier': 'breast_cancer',  # Proxy for spam
                'test_size': 0.2,
                'random_state': 42,
            },
            {
                'problem_slug': 'customer-churn-prediction',
                'loader_type': 'sklearn',
                'dataset_identifier': 'breast_cancer',  # Proxy for churn
                'test_size': 0.2,
                'random_state': 42,
            },
            {
                'problem_slug': 'credit-risk-prediction',
                'loader_type': 'sklearn',
                'dataset_identifier': 'breast_cancer',  # Proxy for credit risk
                'test_size': 0.2,
                'random_state': 42,
            },
            {
                'problem_slug': 'house-price-prediction',
                'loader_type': 'sklearn',
                'dataset_identifier': 'digits',  # Proxy for housing (regression task)
                'test_size': 0.2,
                'random_state': 42,
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for config_data in configs:
                problem_slug = config_data.pop('problem_slug')
                
                try:
                    problem = Problem.objects.get(slug=problem_slug)
                except Problem.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [SKIP] Problem "{problem_slug}" not found in database'
                        )
                    )
                    skipped_count += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'  [DRY RUN] Would create DatasetConfig for {problem.title}:'
                    )
                    for key, value in config_data.items():
                        self.stdout.write(f'    {key}: {value}')
                else:
                    # Create or update DatasetConfig
                    dataset_config, created = DatasetConfig.objects.update_or_create(
                        problem=problem,
                        defaults=config_data
                    )

                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [OK] Created DatasetConfig for {problem.title}'
                            )
                        )
                        created_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [OK] Updated DatasetConfig for {problem.title}'
                            )
                        )
                        updated_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {created_count} created, {updated_count} updated, {skipped_count} skipped'
            )
        )

