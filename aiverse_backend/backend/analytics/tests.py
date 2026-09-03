from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from learner.models import ConceptMastery

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='dash@example.com', username='dashuser', password='pw')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_dashboard_uses_canonical_readiness_thresholds(self):
        ConceptMastery.objects.create(user=self.user, concept_tag='gradient_descent', mastery_score=0.75)
        ConceptMastery.objects.create(user=self.user, concept_tag='linear_algebra', mastery_score=0.60)
        ConceptMastery.objects.create(user=self.user, concept_tag='regression', mastery_score=0.20)

        response = self.client.get('/api/analytics/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['profile']['strong_concepts'], ['gradient_descent'])
        self.assertEqual(response.data['profile']['weak_concepts'], ['linear_algebra', 'regression'])
        by_concept = {item['concept']: item for item in response.data['mastery_breakdown']}
        self.assertEqual(by_concept['gradient_descent']['readiness'], 'satisfied')
        self.assertEqual(by_concept['linear_algebra']['readiness'], 'partially_mastered')
        self.assertEqual(by_concept['regression']['readiness'], 'missing')
