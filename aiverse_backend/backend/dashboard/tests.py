from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserActivity
from ml.models import Problem, Submission
from mentor.models import MentorSession, MentorMessage

User = get_user_model()


class DashboardAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.client.force_authenticate(user=self.user)

    def test_dashboard_overview_requires_auth(self):
        """Test that dashboard requires authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_overview_empty_state(self):
        """Test dashboard with no activity"""
        response = self.client.get('/api/dashboard/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_submissions'], 0)
        self.assertEqual(response.data['success_rate'], 0.0)

    def test_activity_timeline(self):
        """Test activity timeline retrieval"""
        UserActivity.objects.create(
            user=self.user,
            activity_type='video_watched'
        )
        response = self.client.get('/api/dashboard/timeline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_submission_history(self):
        """Test submission history retrieval"""
        response = self.client.get('/api/dashboard/submissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_isolation(self):
        """Test that users only see their own data"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='otheruser'
        )
        UserActivity.objects.create(
            user=other_user,
            activity_type='video_watched'
        )
        response = self.client.get('/api/dashboard/timeline/')
        # Should not include other user's activities
        for activity in response.data['results']:
            self.assertNotEqual(activity['user'], other_user.id)


class UserActivitySignalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )

    def test_mentor_question_creates_activity(self):
        """Test that mentor questions create activity records"""
        session = MentorSession.objects.create(user=self.user)
        initial_count = UserActivity.objects.filter(user=self.user).count()
        
        MentorMessage.objects.create(
            session=session,
            role='user',
            content='What is neural network?'
        )
        
        new_count = UserActivity.objects.filter(user=self.user).count()
        self.assertEqual(new_count, initial_count + 1)
        
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='mentor_question'
        ).first()
        self.assertIsNotNone(activity)