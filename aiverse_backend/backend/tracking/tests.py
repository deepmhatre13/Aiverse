"""
Tests for tracking Celery background tasks.

Covers the four Celery-Beat-scheduled tasks that previously did not exist
(and the deterministic dropout-risk helper), including new-user / empty-history
and graceful-failure cases. The external ML-service call is mocked to avoid
network access in tests.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from learner.models import ConceptMastery, LearnerProfile
from recommendations.models import Recommendation

from tracking.tasks import (
    _compute_dropout_risk,
    generate_daily_recommendations_for_all,
    recompute_all_mastery_scores,
    retrain_ml_models_nightly,
    update_dropout_risk_all_users,
)

User = get_user_model()


class DropoutRiskComputeTests(TestCase):
    """Unit tests for the deterministic _compute_dropout_risk helper."""

    def _mk(self, last_login_days=0, last_active_days=0, engagement=0.0,
            frustration=0.0, lessons=0, problems=0, quizzes=0):
        user = User.objects.create_user(
            email=f"dropout_{abs(hash((last_login_days, lessons, engagement)))}@example.com",
            username=f"dropout_{abs(hash((last_login_days, engagement)))}",
            password="x",
            last_login=timezone.now() - timedelta(days=last_login_days),
        )
        profile = LearnerProfile.objects.create(
            user=user,
            last_active=timezone.now() - timedelta(days=last_active_days),
            engagement_score=engagement,
            frustration_score=frustration,
            total_lessons_completed=lessons,
            total_problems_solved=problems,
            total_quizzes_passed=quizzes,
        )
        return user, profile

    def test_risk_is_bounded_0_to_1(self):
        user = User.objects.create_user(
            email="bounded@example.com", username="bounded", password="x"
        )
        profile = LearnerProfile.objects.create(user=user)
        risk = _compute_dropout_risk(profile, user)
        self.assertGreaterEqual(risk, 0.0)
        self.assertLessEqual(risk, 1.0)

    def test_inactive_new_user_has_high_risk(self):
        user, profile = self._mk(last_login_days=30, last_active_days=30)
        risk = _compute_dropout_risk(profile, user)
        # inactivity=1.0, engagement=0, low-activity=1.0 -> high risk (>0.5)
        self.assertGreater(risk, 0.5)

    def test_active_engaged_user_has_low_risk(self):
        user, profile = self._mk(
            last_login_days=0, last_active_days=0,
            engagement=1.0, lessons=10, problems=5, quizzes=3,
        )
        risk = _compute_dropout_risk(profile, user)
        # inactivity=0, frustration=0, engagement=1, not low-activity -> ~0
        self.assertLess(risk, 0.3)


class RecommendationBatchTaskTests(TestCase):
    """generate_daily_recommendations_for_all"""

    def test_new_user_no_fabricated_recommendations(self):
        User.objects.create_user(
            email="rec@example.com", username="recuser", password="x",
            last_login=timezone.now(),
        )
        result = generate_daily_recommendations_for_all()
        self.assertEqual(result["status"], "success")
        # A user with no history / no masteries must not receive fake recs.
        self.assertEqual(Recommendation.objects.count(), 0)

    def test_inactive_users_are_skipped(self):
        """Active filter (last 7 days) should skip stale users."""
        User.objects.create_user(
            email="stale@example.com", username="staleuser", password="x",
            last_login=timezone.now() - timedelta(days=60),
        )
        result = generate_daily_recommendations_for_all()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["generated"], 0)

class DropoutRiskBatchTaskTests(TestCase):
    """update_dropout_risk_all_users"""

    def test_active_user_gets_dropout_risk_set(self):
        user = User.objects.create_user(
            email="dr@example.com", username="druser", password="x",
            last_login=timezone.now(),
        )
        result = update_dropout_risk_all_users()
        self.assertEqual(result["status"], "success")
        profile = LearnerProfile.objects.get(user=user)
        self.assertGreaterEqual(profile.dropout_risk, 0.0)
        self.assertLessEqual(profile.dropout_risk, 1.0)


class RecomputedMasteryBatchTaskTests(TestCase):
    """recompute_all_mastery_scores"""

    def test_runs_for_active_user(self):
        user = User.objects.create_user(
            email="rm@example.com", username="rmuser", password="x",
            last_login=timezone.now(),
        )
        ConceptMastery.objects.create(
            user=user, concept_tag="classification", mastery_score=0.5
        )
        result = recompute_all_mastery_scores()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["updated"], 1)

    def test_empty_history_runs_cleanly(self):
        User.objects.create_user(
            email="rm2@example.com", username="rm2user", password="x",
            last_login=timezone.now(),
        )
        result = recompute_all_mastery_scores()
        self.assertEqual(result["status"], "success")


class RetrainMLModelsTaskTests(TestCase):
    """retrain_ml_models_nightly — external call mocked."""

    @mock.patch("recommendations.ml_client.call_ml_service", return_value=None)
    def test_graceful_when_service_unavailable(self, _mock_call):
        result = retrain_ml_models_nightly()
        self.assertEqual(result["status"], "unavailable")
        _mock_call.assert_called_once()

    @mock.patch(
        "recommendations.ml_client.call_ml_service",
        return_value={"retrained": ["bkt", "irt"], "status": "ok"},
    )
    def test_reports_retrained_models(self, _mock_call):
        result = retrain_ml_models_nightly()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["retrained"], ["bkt", "irt"])

