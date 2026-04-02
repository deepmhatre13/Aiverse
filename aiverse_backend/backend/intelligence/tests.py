from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from intelligence.models import ExperimentRun, SuggestionLog, UserProfile
from intelligence.services.profile_engine import update_user_profile
from intelligence.services.suggestion_engine import generate_suggestions


class ProfileEngineTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="profile-tests@example.com",
            username="profile-tests",
            password="secret123",
        )

    def _run(self, *, accuracy, model_type, task_type, minutes_ago):
        run = ExperimentRun.objects.create(
            user=self.user,
            dataset_name="dataset",
            model_type=model_type,
            hyperparameters={},
            accuracy=accuracy,
            loss=0.1,
            task_type=task_type,
        )
        ExperimentRun.objects.filter(pk=run.pk).update(
            created_at=timezone.now() - timedelta(minutes=minutes_ago)
        )

    def test_update_user_profile_applies_rules(self):
        self._run(accuracy=0.90, model_type="random_forest", task_type="classification", minutes_ago=5)
        self._run(accuracy=0.88, model_type="random_forest", task_type="classification", minutes_ago=4)
        self._run(accuracy=0.86, model_type="random_forest", task_type="classification", minutes_ago=3)
        self._run(accuracy=0.50, model_type="svm", task_type="regression", minutes_ago=2)
        self._run(accuracy=0.60, model_type="svm", task_type="regression", minutes_ago=1)

        profile = update_user_profile(self.user)

        self.assertIsNotNone(profile)
        self.assertEqual(profile.total_runs, 5)
        self.assertAlmostEqual(profile.avg_score, 0.748, places=3)
        self.assertEqual(profile.skill_level, UserProfile.SKILL_INTERMEDIATE)
        self.assertIn("classification", profile.strengths)
        self.assertIn("regression", profile.weaknesses)
        self.assertIn("model:svm", profile.weaknesses)
        self.assertEqual(profile.preferred_models[:2], ["random_forest", "svm"])

    def test_profile_update_cooldown_prevents_recompute_until_window_expires(self):
        self._run(accuracy=0.50, model_type="svm", task_type="regression", minutes_ago=2)
        profile = update_user_profile(self.user)
        self.assertEqual(profile.total_runs, 1)
        self.assertAlmostEqual(profile.avg_score, 0.50, places=3)

        self._run(accuracy=0.95, model_type="random_forest", task_type="classification", minutes_ago=1)
        stale_profile = update_user_profile(self.user)
        self.assertEqual(stale_profile.total_runs, 1)

        cache.delete(f"intelligence:profile_update:cooldown:{self.user.pk}")
        refreshed = update_user_profile(self.user)
        self.assertEqual(refreshed.total_runs, 2)
        self.assertAlmostEqual(refreshed.avg_score, 0.725, places=3)


class SuggestionEngineTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="suggestion-tests@example.com",
            username="suggestion-tests",
            password="secret123",
        )

    def _run(self, *, accuracy, model_type, minutes_ago, hyperparameters=None):
        run = ExperimentRun.objects.create(
            user=self.user,
            dataset_name="dataset",
            model_type=model_type,
            hyperparameters=hyperparameters or {},
            accuracy=accuracy,
            loss=0.2,
            task_type="classification",
        )
        ExperimentRun.objects.filter(pk=run.pk).update(
            created_at=timezone.now() - timedelta(minutes=minutes_ago)
        )

    def test_generate_suggestions_applies_rules_and_hourly_dedupe(self):
        self._run(accuracy=0.60, model_type="logistic_regression", minutes_ago=5)
        self._run(accuracy=0.64, model_type="logistic_regression", minutes_ago=4)
        self._run(accuracy=0.649, model_type="logistic_regression", minutes_ago=3)
        self._run(accuracy=0.650, model_type="logistic_regression", minutes_ago=2)
        self._run(
            accuracy=0.6505,
            model_type="logistic_regression",
            minutes_ago=1,
            hyperparameters={"train_accuracy": 0.95, "test_accuracy": 0.70},
        )

        suggestions = generate_suggestions(self.user)
        suggestion_types = {row["suggestion_type"] for row in suggestions}

        self.assertIn("overfitting", suggestion_types)
        self.assertIn("low_accuracy", suggestion_types)
        self.assertIn("plateau", suggestion_types)
        self.assertIn("model_bias", suggestion_types)
        first_count = SuggestionLog.objects.filter(user=self.user).count()
        self.assertGreaterEqual(first_count, 4)

        cache.delete(f"intelligence:suggestions:cooldown:{self.user.pk}")
        generate_suggestions(self.user)
        second_count = SuggestionLog.objects.filter(user=self.user).count()
        self.assertEqual(second_count, first_count)

        SuggestionLog.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        cache.delete(f"intelligence:suggestions:cooldown:{self.user.pk}")
        generate_suggestions(self.user)
        third_count = SuggestionLog.objects.filter(user=self.user).count()
        self.assertGreater(third_count, second_count)


class BackfillProfilesCommandTests(TestCase):
    def test_backfill_user_profiles_command_creates_missing_profiles(self):
        User = get_user_model()
        user1 = User.objects.create_user(email="legacy-1@example.com", username="legacy1", password="secret123")
        user2 = User.objects.create_user(email="legacy-2@example.com", username="legacy2", password="secret123")

        UserProfile.objects.filter(user=user1).delete()
        UserProfile.objects.filter(user=user2).delete()

        self.assertFalse(UserProfile.objects.filter(user=user1).exists())
        self.assertFalse(UserProfile.objects.filter(user=user2).exists())

        call_command("backfill_user_profiles")

        self.assertTrue(UserProfile.objects.filter(user=user1).exists())
        self.assertTrue(UserProfile.objects.filter(user=user2).exists())

    def test_backfill_user_profiles_dry_run_does_not_create_profiles(self):
        User = get_user_model()
        user = User.objects.create_user(email="legacy-3@example.com", username="legacy3", password="secret123")
        UserProfile.objects.filter(user=user).delete()

        call_command("backfill_user_profiles", "--dry-run")

        self.assertFalse(UserProfile.objects.filter(user=user).exists())
