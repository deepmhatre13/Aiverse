"""
Load all 40 production-grade ML problems into learn.CodingProblem.

Usage:
    python manage.py load_problems
    python manage.py load_problems --clear
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from learn.models import CodingProblem
from learn.data.problems_catalog import PROBLEMS


class Command(BaseCommand):
    help = 'Load 40 production-grade ML coding problems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing problems before loading',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = CodingProblem.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing problems'))

        created = 0
        updated = 0
        for order, problem in enumerate(PROBLEMS, start=1):
            defaults = {
                'title': problem['title'],
                'difficulty': problem['difficulty'],
                'category': problem.get('category', 'Fundamentals'),
                'concept_tag': problem.get('concept_tag', 'classification'),
                'metric': problem.get('metric', 'ACCURACY'),
                'points': problem.get('points', 800),
                'description': problem.get('description', ''),
                'starter_code': problem.get('starter_code', ''),
                'test_cases': problem.get('test_cases', []),
                'expected_output_format': problem.get('expected_output_format', ''),
                'constraints': problem.get('constraints', []),
                'hints': problem.get('hints', []),
                'tags': problem.get('tags', problem.get('concept_tags', [])),
                'is_active': True,
                'order': order,
            }
            _, was_created = CodingProblem.objects.update_or_create(
                slug=problem['slug'],
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        total = CodingProblem.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded problems: {created} created, {updated} updated. Total active: {total}'
            )
        )
