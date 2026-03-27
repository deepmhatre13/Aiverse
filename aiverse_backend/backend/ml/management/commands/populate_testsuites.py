"""
Management command to populate TestSuite from existing test_cases.py definitions.

Usage:
    python manage.py populate_testsuites
"""

import json
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ml.models import Problem, TestSuite
from ml.test_cases import (
    PROBLEM_TEST_SUITES,
    ProblemTestSuite,
    TestCase,
)


def serialize_test_case(test_case: TestCase) -> dict:
    """
    Serialize a TestCase to JSON-safe dict.
    
    Note: We store metadata (shape, metric, threshold) but not actual data.
    Actual data will be loaded from test_cases.py at execution time.
    """
    return {
        "name": test_case.name,
        "metric": test_case.metric,
        "threshold": float(test_case.threshold),
        "X_train_shape": list(test_case.X_train.shape),
        "y_train_shape": list(test_case.y_train.shape) if hasattr(test_case.y_train, 'shape') else [len(test_case.y_train)],
        "X_test_shape": list(test_case.X_test.shape),
        "y_test_shape": list(test_case.y_test.shape) if hasattr(test_case.y_test, 'shape') else [len(test_case.y_test)],
    }


def serialize_test_suite(test_suite: ProblemTestSuite) -> tuple:
    """
    Serialize a ProblemTestSuite to JSON-safe lists.
    
    Returns:
        (public_tests_json, private_tests_json) - both are lists of dicts
    """
    public_tests = [serialize_test_case(tc) for tc in test_suite.public_tests]
    private_tests = [serialize_test_case(tc) for tc in test_suite.private_tests]
    return public_tests, private_tests


class Command(BaseCommand):
    help = 'Populate TestSuite database from test_cases.py definitions'

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

        # Get all active problems
        problems = Problem.objects.filter(is_active=True)
        
        if not problems.exists():
            self.stdout.write(self.style.ERROR('No active problems found in database'))
            return

        self.stdout.write(f'Found {problems.count()} active problems')

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        with transaction.atomic():
            for problem in problems:
                # Look up test suite in PROBLEM_TEST_SUITES
                test_suite_def = PROBLEM_TEST_SUITES.get(problem.slug)

                if not test_suite_def:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⊘ {problem.slug}: No test suite defined in test_cases.py'
                        )
                    )
                    skipped_count += 1
                    continue

                try:
                    # Serialize test cases to JSON
                    public_tests_json, private_tests_json = serialize_test_suite(test_suite_def)

                    if not dry_run:
                        # Create or update TestSuite
                        test_suite, created = TestSuite.objects.get_or_create(
                            problem=problem,
                            defaults={
                                'public_tests': public_tests_json,
                                'private_tests': private_tests_json,
                            }
                        )

                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ {problem.slug}: Created TestSuite ({len(public_tests_json)} public, {len(private_tests_json)} private)'
                                )
                            )
                            created_count += 1
                        else:
                            test_suite.public_tests = public_tests_json
                            test_suite.private_tests = private_tests_json
                            test_suite.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ {problem.slug}: Updated TestSuite ({len(public_tests_json)} public, {len(private_tests_json)} private)'
                                )
                            )
                            updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ {problem.slug}: Would create TestSuite ({len(public_tests_json)} public, {len(private_tests_json)} private)'
                            )
                        )
                        created_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ {problem.slug}: Error - {str(e)}'
                        )
                    )
                    error_count += 1

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write('SUMMARY')
        self.stdout.write('='*70)
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Errors:  {error_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN MODE - No changes were made'))
        else:
            total = created_count + updated_count
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully processed {total} test suites!')
            )
