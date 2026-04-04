from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegisterTests(APITestCase):
	def test_register_with_full_name_without_username(self):
		payload = {
			'email': 'newuser@example.com',
			'password': 'StrongPass1',
			'full_name': 'New User',
		}

		response = self.client.post(reverse('register'), payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('user', response.data)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)
		self.assertIn('tokens', response.data)
		self.assertIn('access', response.data['tokens'])
		self.assertIn('refresh', response.data['tokens'])

		user = User.objects.get(email='newuser@example.com')
		self.assertEqual(user.display_name, 'New User')
		self.assertTrue(user.username)

	def test_register_generates_unique_username_when_base_taken(self):
		User.objects.create_user(
			email='existing@example.com',
			password='StrongPass1',
			username='john',
		)

		payload = {
			'email': 'john@example.com',
			'password': 'StrongPass1',
			'full_name': 'John Two',
		}

		response = self.client.post(reverse('register'), payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = User.objects.get(email='john@example.com')
		self.assertNotEqual(created.username, 'john')
		self.assertTrue(created.username.startswith('john'))

	def test_register_rejects_case_insensitive_duplicate_email(self):
		User.objects.create_user(
			email='existing@example.com',
			password='StrongPass1',
			username='existing',
		)

		payload = {
			'email': 'EXISTING@example.com',
			'password': 'StrongPass1',
			'full_name': 'Existing User',
		}

		response = self.client.post(reverse('register'), payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('email', response.data)
