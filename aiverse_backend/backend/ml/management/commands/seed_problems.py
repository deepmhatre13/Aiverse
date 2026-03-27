import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from ml.models import Problem


class Command(BaseCommand):
    help = "Seed ML problems into the database"

    def handle(self, *args, **options):

        problems_data = [
            {
                "title": "Iris Species Classification",
                "slug": "iris-species-classification",
                "description": "Iris classification problem",
                "problem_type": "classification",
                "metric": "accuracy",
                "difficulty": "easy",
                "target_column": "species",
                "dataset_dir": os.path.join(settings.BASE_DIR, "datasets", "iris"),
            },
            {
                "title": "Spam Detection",
                "slug": "spam-detection",
                "description": "Spam detection problem",
                "problem_type": "classification",
                "metric": "f1",
                "difficulty": "medium",
                "target_column": "is_spam",
                "dataset_dir": os.path.join(settings.BASE_DIR, "datasets", "spam"),
            },
            {
                "title": "Customer Churn Prediction",
                "slug": "customer-churn-prediction",
                "description": "Churn prediction problem",
                "problem_type": "classification",
                "metric": "f1",
                "difficulty": "medium",
                "target_column": "churn",
                "dataset_dir": os.path.join(settings.BASE_DIR, "datasets", "churn"),
            },
            {
                "title": "Credit Risk Prediction",
                "slug": "credit-risk-prediction",
                "description": "Credit risk problem",
                "problem_type": "classification",
                "metric": "accuracy",
                "difficulty": "hard",
                "target_column": "default",
                "dataset_dir": os.path.join(settings.BASE_DIR, "datasets", "credit"),
            },
            {
                "title": "House Price Prediction",
                "slug": "house-price-prediction",
                "description": "House price regression problem",
                "problem_type": "regression",
                "metric": "rmse",
                "difficulty": "medium",
                "target_column": "price",
                "dataset_dir": os.path.join(settings.BASE_DIR, "datasets", "houses"),
            },
        ]

        with transaction.atomic():
            for data in problems_data:
                problem = Problem.objects.create(**data)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Inserted {problem.title} (id={problem.id})")
                )

        self.stdout.write(self.style.SUCCESS("✓ All problems committed"))
