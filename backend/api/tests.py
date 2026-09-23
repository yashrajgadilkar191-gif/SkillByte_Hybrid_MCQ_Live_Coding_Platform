from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckAPITests(SimpleTestCase):
    """
    Test suite for Phase 1 Health Check and Frontend views.
    Inherits SimpleTestCase so it does not require database connection.
    """

    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint_returns_ok(self):
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            "status": "ok",
            "service": "SkillByte API"
        })

    def test_frontend_home_view_returns_ok(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'SKILLBYTE')
        self.assertContains(response, 'Where Theory Meets Practice')

    def test_frontend_login_view_returns_ok(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Welcome Back')
        self.assertContains(response, 'student@example.com')

    def test_frontend_register_view_returns_ok(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'Student Registration')

    def test_frontend_dashboard_view_returns_ok(self):
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Available Assessments')

    def test_frontend_mcq_setup_view_returns_ok(self):
        url = reverse('mcq_setup_page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Select MCQ Subject & Difficulty')

    def test_frontend_mcq_assessment_view_returns_ok(self):
        url = reverse('mcq_assessment_page', kwargs={'attempt_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Question Palette')

    def test_frontend_mcq_result_view_returns_ok(self):
        url = reverse('mcq_result_page', kwargs={'attempt_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Assessment Performance Report')

