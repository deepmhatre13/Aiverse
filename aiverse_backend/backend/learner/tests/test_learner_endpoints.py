"""
Tests for the learner app frontend-contract endpoints.

Covers:
- GET /api/learner/profile/
- GET /api/learner/mastery/
- GET /api/learner/mastery-history/

Includes new-user / empty-history and missing-parameter cases.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from learner.models import ConceptMastery, LearnerProfile

User = get_user_model()


class LearnerProfileEndpointTests(APITestCase):
    """GET /api/learner/profile/"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com", username="profileuser", password="x"
        )
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/learner/profile/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_user_gets_deterministic_default(self):
        """User with no history must get defaults, not fabricated data."""
        resp = self.client.get("/api/learner/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["estimated_skill_level"], "beginner")
        self.assertEqual(resp.data["overall_mastery"], 0.0)
        self.assertEqual(resp.data["weak_concepts"], [])
        self.assertEqual(resp.data["strong_concepts"], [])

    def test_profile_reflects_persisted_values(self):
        profile = LearnerProfile.objects.create(
            user=self.user,
            estimated_skill_level="intermediate",
            overall_mastery=0.71,
            weak_concepts=["classification"],
            strong_concepts=["python_ml"],
        )
        resp = self.client.get("/api/learner/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["estimated_skill_level"], "intermediate")
        self.assertEqual(resp.data["overall_mastery"], 0.71)
        self.assertEqual(resp.data["weak_concepts"], ["classification"])
        self.assertEqual(resp.data["strong_concepts"], ["python_ml"])


class LearnerMasteryEndpointTests(APITestCase):
    """GET /api/learner/mastery/ — returns an array of mastery records."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="mastery@example.com", username="masteryuser", password="x"
        )
        self.client.force_authenticate(user=self.user)

    def test_empty_history_returns_empty_array(self):
        resp = self.client.get("/api/learner/mastery/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_returns_mastery_records(self):
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag="classification",
            mastery_score=0.45,
            is_struggling=True,
        )
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag="python_ml",
            mastery_score=0.94,
            is_struggling=False,
        )
        resp = self.client.get("/api/learner/mastery/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        by_tag = {r["concept_tag"]: r for r in resp.data}
        self.assertEqual(by_tag["classification"]["mastery_score"], 0.45)
        self.assertTrue(by_tag["classification"]["is_struggling"])
        self.assertEqual(by_tag["python_ml"]["mastery_score"], 0.94)
        self.assertFalse(by_tag["python_ml"]["is_struggling"])


class LearnerMasteryHistoryEndpointTests(APITestCase):
    """GET /api/learner/mastery-history/?concept=X"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="history@example.com", username="historyuser", password="x"
        )
        self.client.force_authenticate(user=self.user)

    def test_missing_concept_returns_400(self):
        resp = self.client.get("/api/learner/mastery-history/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_history_returns_empty_trace(self):
        resp = self.client.get("/api/learner/mastery-history/?concept=classification")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["trace"], [])
        self.assertEqual(resp.data["current_mastery"], 0.0)
        self.assertEqual(resp.data["concept_tag"], "classification")

    def test_returns_persisted_bkt_trace(self):
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag="classification",
            mastery_score=0.5,
            bkt_trace=[0.10, 0.30, 0.50],
        )
        resp = self.client.get("/api/learner/mastery-history/?concept=classification")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["trace"], [0.10, 0.30, 0.50])
        self.assertEqual(resp.data["current_mastery"], 0.5)


class LearnerPrerequisiteEndpointTests(APITestCase):
    """GET /api/learner/prerequisites/?concept=X"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="prereq@example.com", username="prerequser", password="x"
        )
        self.client.force_authenticate(user=self.user)

    def test_missing_concept_parameter_returns_400(self):
        resp = self.client.get("/api/learner/prerequisites/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_user_reads_unknown_prerequisites(self):
        resp = self.client.get("/api/learner/prerequisites/?concept=neural_networks")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("prerequisites", resp.data)
        self.assertIn("recommended_next", resp.data)
        self.assertTrue(all(item["readiness"] == "unknown" for item in resp.data["prerequisites"]))
        self.assertTrue(all(item["status"] == "unknown" for item in resp.data["prerequisites"]))