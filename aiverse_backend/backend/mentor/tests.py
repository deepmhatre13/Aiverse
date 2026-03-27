from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import MentorSession, MentorMessage

User = get_user_model()


class MentorAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_session(self):
        """Test creating a new mentor session"""
        response = self.client.post('/api/mentor/session/start/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(MentorSession.objects.count(), 1)

    def test_ask_question_requires_auth(self):
        """Test that asking requires authentication"""
        self.client.force_authenticate(user=None)
        session = MentorSession.objects.create(user=self.user)
        response = self.client.post(
            f'/api/mentor/session/{session.id}/ask/',
            {'question': 'What is gradient descent?'}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ask_question_validation(self):
        """Test question length validation"""
        session = MentorSession.objects.create(user=self.user)
        response = self.client.post(
            f'/api/mentor/session/{session.id}/ask/',
            {'question': 'short'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_messages(self):
        """Test retrieving session messages"""
        session = MentorSession.objects.create(user=self.user)
        MentorMessage.objects.create(
            session=session,
            role='user',
            content='What is backpropagation?'
        )
        response = self.client.get(f'/api/mentor/session/{session.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_can_only_access_own_sessions(self):
        """Test session isolation between users"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            username='otheruser'
        )
        other_session = MentorSession.objects.create(user=other_user)
        response = self.client.get(f'/api/mentor/session/{other_session.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)