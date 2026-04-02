from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from intelligence.models import UserProfile


class Command(BaseCommand):
    help = "Create missing intelligence UserProfile rows for legacy users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many profiles would be created without writing changes.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Bulk create batch size (default: 1000).",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        batch_size = int(options.get("batch_size") or 1000)

        User = get_user_model()
        missing_user_ids = list(
            User.objects.filter(intelligence_profile__isnull=True)
            .order_by("id")
            .values_list("id", flat=True)
        )

        missing_count = len(missing_user_ids)
        if missing_count == 0:
            self.stdout.write(self.style.SUCCESS("No missing user profiles found."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {missing_count} missing user profiles would be created."
                )
            )
            return

        to_create = [UserProfile(user_id=user_id) for user_id in missing_user_ids]
        created = UserProfile.objects.bulk_create(
            to_create,
            ignore_conflicts=True,
            batch_size=batch_size,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill completed. Created {len(created)} profiles (requested {missing_count})."
            )
        )
