"""Integration tests: event -> ConceptMastery -> LearnerProfile (Phase 2 hot path).

Verifies that processing a learner event updates BKT mastery AND refreshes the
canonical LearnerProfile synchronously (closing the loop that previously only
ran in the nightly batch).
"""
from unittest import mock

from django.test import TestCase
from django.contrib.auth import get_user_model

from learner.models import ConceptMastery, LearnerProfile
from learner.tasks import process_event_for_mastery
from tracking.models import LearnerEvent

User = get_user_model()


class EventToMasteryToProfileTests(TestCase):
    def setUp(self):
                self.user = User.objects.create_user(email="alice@example.com", username="alice", password="pw")

    @mock.patch('learner.tasks.recalculate_learning_path')
    def test_quiz_passed_updates_mastery_and_refreshes_profile(self, _mock_recalc):
        LearnerEvent.objects.create(
            user=self.user,
            event_type='QUIZ_PASSED',
            content_type='quiz',
            content_id=1,
            metadata={'concept_tag': 'classification', 'score': 0.9},
        )
        event = LearnerEvent.objects.get(event_type='QUIZ_PASSED')
        result = process_event_for_mastery(str(event.id))

        self.assertEqual(result.get('status'), 'success')

        mastery = ConceptMastery.objects.get(user=self.user, concept_tag='classification')
        self.assertEqual(mastery.quiz_attempts, 1)
        self.assertEqual(mastery.coding_attempts, 0)
        self.assertGreater(mastery.mastery_score, 0.0)
        self.assertLessEqual(mastery.mastery_score, 1.0)

        # Canonical LearnerProfile refreshed on the hot path (not nightly-only).
        profile = LearnerProfile.objects.get(user=self.user)
        self.assertAlmostEqual(profile.overall_mastery, mastery.mastery_score, places=3)
        # With a single mastery of ~0.64 (< 0.8, >= 0.5) the analyzer classifies
        # the learner as intermediate -- neither weak (< 0.5) nor strong (>= 0.8).
        self.assertEqual(profile.estimated_skill_level, "intermediate")

        # Existing learning-path recalc trigger still fires for passed events.
        _mock_recalc.delay.assert_called_once_with(self.user.id)
