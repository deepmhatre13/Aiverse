"""
Management command to reset ML problems to HackerRank style.

This command:
1. Deletes all legacy problems (iris, spam, churn, credit, house price)
2. Deletes all associated submissions
3. Creates ONLY the 3 HackerRank-style problems from registry
4. Ensures a clean slate for the new ML system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from ml.models import Problem, Submission
from ml.registry import list_problems


class Command(BaseCommand):
    help = "Reset ML problems to HackerRank-style registry-based system"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Step 1: Show what will be deleted
        existing_problems = Problem.objects.all()
        legacy_slugs = [
            'iris-species-classification',
            'spam-detection',
            'customer-churn-prediction',
            'credit-risk-prediction',
            'house-price-prediction',
        ]

        if existing_problems.exists():
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  This will DELETE {existing_problems.count()} existing problems and all their submissions."
            ))
            self.stdout.write(self.style.WARNING("Problems to delete:"))
            for problem in existing_problems:
                sub_count = problem.submissions.count()
                self.stdout.write(f"  - {problem.slug} ({sub_count} submissions)")

            if not force:
                confirm = input("\nProceed? (yes/no): ")
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR("❌ Aborted"))
                    return

        # Step 2: Delete everything
        with transaction.atomic():
            # Delete submissions first (FK constraint)
            submission_count = Submission.objects.all().count()
            if submission_count > 0:
                Submission.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f"✓ Deleted {submission_count} submissions"))

            # Delete problems
            problem_count = Problem.objects.all().count()
            if problem_count > 0:
                Problem.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f"✓ Deleted {problem_count} problems"))

            # Step 3: Create the 3 new problems from registry
            registry_problems = list_problems()
            for registry_problem in registry_problems:
                problem = Problem.objects.create(
                    title=registry_problem.title,
                    slug=registry_problem.slug,
                    description=registry_problem.description[:500],  # Truncate for DB
                    problem_type=registry_problem.task_type,
                    metric=registry_problem.default_metric,
                    difficulty=getattr(registry_problem, 'difficulty', 'medium'),
                    difficulty_rating=getattr(registry_problem, 'difficulty_rating', 1200),
                    target_column='predictions',  # Not used in registry-based system
                    dataset_dir='',  # Not used in registry-based system
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created {problem.title} ({problem.slug})")
                )

        self.stdout.write(self.style.SUCCESS("\n✅ ML problems reset complete!"))
        self.stdout.write(self.style.SUCCESS("   - 3 HackerRank-style problems ready"))
        self.stdout.write(self.style.SUCCESS("   - All legacy data deleted"))
        self.stdout.write(self.style.SUCCESS("   - System ready for testing"))
