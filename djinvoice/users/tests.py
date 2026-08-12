from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class UserRegisterTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('user-register')
        self.valid_payload = {
            'email': 'testuser@example.com',
            'username': 'testuser',
            'password': 'password123',
            'password2': 'password123'
        }

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], self.valid_payload['email'])
        self.assertEqual(response.data['username'], self.valid_payload['username'])
        self.assertTrue(User.objects.filter(email=self.valid_payload['email']).exists())

    def test_register_user_password_mismatch(self):
        payload = self.valid_payload.copy()
        payload['password2'] = 'differentpassword'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('Las contraseñas no coinciden.', response.data['non_field_errors'][0])

    def test_register_user_existing_email(self):
        # Create user first
        User.objects.create_user(
            email=self.valid_payload['email'],
            username=self.valid_payload['username'],
            password=self.valid_payload['password']
        )
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('user with this email already exists.', response.data['email'][0])

    def test_register_user_password_too_short(self):
        payload = self.valid_payload.copy()
        payload['password'] = 'short'
        payload['password2'] = 'short'
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class UserLoginTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('user-login')
        self.email = 'loginuser@example.com'
        self.username = 'loginuser'
        self.password = 'securepassword123'
        self.user = User.objects.create_user(
            email=self.email,
            username=self.username,
            password=self.password
        )

    def test_login_success(self):
        payload = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data)
        self.assertIn('username', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], self.email)
        self.assertEqual(response.data['username'], self.username)

    def test_login_invalid_credentials(self):
        payload = {
            'email': self.email,
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertIn('Credenciales inválidas.', response.data['non_field_errors'][0])

class RefreshTokenTests(APITestCase):
    def setUp(self):
        self.refresh_url = reverse('user-refresh')
        self.email = 'refreshuser@example.com'
        self.username = 'refreshuser'
        self.password = 'securepassword123'
        self.user = User.objects.create_user(
            email=self.email,
            username=self.username,
            password=self.password
        )
    def test_refresh_token_success(self):
        # First, log in to get a refresh token
        login_url = reverse('user-login')
        login_payload = {
            'email': self.email,
            'password': self.password
        }
        login_response = self.client.post(login_url, login_payload, format='json')
        refresh_token = login_response.data['refresh']

        # Now, use the refresh token to get a new access token
        refresh_payload = {
            'refresh': refresh_token
        }
        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_missing(self):
        response = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Refresh token is required.')
    
    def test_refresh_token_invalid(self):
        refresh_payload = {
            'refresh': 'invalidtoken'
        }
        response = self.client.post(self.refresh_url, refresh_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid refresh token.')