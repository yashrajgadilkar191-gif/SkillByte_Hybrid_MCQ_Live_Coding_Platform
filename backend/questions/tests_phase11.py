"""
Phase 11 Automated Tests: Student Profile, Password Change, Assessment Lifecycle,
Solution Utilities, Admin Analytics Export, and Platform Hardening.
Verifies:
1. Student profile updating (PATCH /api/auth/me/) and duplicate email validation.
2. Secure password change (POST /api/auth/change-password/) with old password check and matching confirmation.
3. Assessment abandonment (POST /api/assessments/<id>/abandon/) with state validation and ownership check.
4. Active assessment detection (GET /api/assessments/active/) for resume capabilities.
5. Admin analytics CSV export (GET /api/admin/analytics/export/) RBAC protection and CSV formatting.
6. Custom branded error views (404, 403, 500) rendering.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile, Role
from questions.models import (
    Question,
    QuestionType,
    Category,
    DifficultyLevel,
    AssessmentAttempt,
    AssessmentResult,
    AttemptStatus,
)
from api.views import custom_404_view, custom_403_view, custom_500_view


class Phase11ComprehensiveTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = RequestFactory()

        # Admin user
        self.admin = User.objects.create_user(
            username='admin_phase11',
            email='admin11@skillbyte.test',
            password='AdminPassword123!'
        )
        self.admin.profile.role = Role.ADMIN
        self.admin.profile.save()

        # Student 1 (Alice)
        self.alice = User.objects.create_user(
            username='alice_phase11',
            email='alice11@skillbyte.test',
            password='AlicePassword123!',
            first_name='Alice',
            last_name='Smith'
        )
        self.alice.profile.role = Role.STUDENT
        self.alice.profile.save()

        # Student 2 (Bob)
        self.bob = User.objects.create_user(
            username='bob_phase11',
            email='bob11@skillbyte.test',
            password='BobPassword123!',
            first_name='Bob',
            last_name='Jones'
        )
        self.bob.profile.role = Role.STUDENT
        self.bob.profile.save()

        self.alice_token = str(RefreshToken.for_user(self.alice).access_token)
        self.bob_token = str(RefreshToken.for_user(self.bob).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

        # Question fixture
        self.question = Question.objects.create(
            title='Phase 11 Test Question',
            description='Test question for attempt lifecycle',
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            is_active=True
        )

    # 1. Student update profile success
    def test_student_update_profile_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.patch('/api/auth/me/', {
            'first_name': 'Alicia',
            'last_name': 'Wonderland',
            'email': 'alicia.updated@skillbyte.test'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.first_name, 'Alicia')
        self.assertEqual(self.alice.last_name, 'Wonderland')
        self.assertEqual(self.alice.email, 'alicia.updated@skillbyte.test')

    # 2. Student update profile duplicate email rejected
    def test_student_update_profile_duplicate_email(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.patch('/api/auth/me/', {
            'email': self.bob.email
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    # 3. Student change password success
    def test_student_change_password_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'AlicePassword123!',
            'new_password': 'NewSecretPassword456!',
            'new_password_confirm': 'NewSecretPassword456!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password('NewSecretPassword456!'))

    # 4. Student change password invalid current password
    def test_student_change_password_invalid_current(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'WrongCurrentPassword!',
            'new_password': 'NewSecretPassword456!',
            'new_password_confirm': 'NewSecretPassword456!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    # 5. Student change password mismatch
    def test_student_change_password_mismatch(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post('/api/auth/change-password/', {
            'old_password': 'AlicePassword123!',
            'new_password': 'NewSecretPassword456!',
            'new_password_confirm': 'DifferentPassword789!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password_confirm', response.data)

    # 6. Abandon active attempt success
    def test_abandon_active_attempt_success(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS,
            max_score=10,
            time_limit_seconds=600
        )
        attempt.questions.add(self.question)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post(f'/api/assessments/{attempt.id}/abandon/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, AttemptStatus.ABANDONED)
        self.assertIsNotNone(attempt.submitted_at)

    # 7. Abandon completed attempt rejected
    def test_abandon_completed_attempt_rejected(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            max_score=10,
            total_score=10.0,
            time_limit_seconds=600,
            submitted_at=timezone.now()
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post(f'/api/assessments/{attempt.id}/abandon/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot abandon assessment', response.data.get('error', ''))

    # 8. Abandon unowned attempt forbidden
    def test_abandon_unowned_attempt_forbidden(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.bob,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS,
            max_score=10,
            time_limit_seconds=600
        )

        # Alice tries to abandon Bob's attempt
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.post(f'/api/assessments/{attempt.id}/abandon/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, AttemptStatus.IN_PROGRESS)

    # 9. Active attempt detection
    def test_active_attempt_detection(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS,
            max_score=10,
            time_limit_seconds=600
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.get('/api/assessments/active/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('has_active_attempt'))
        self.assertIsNotNone(response.data.get('attempt'))
        self.assertEqual(response.data['attempt']['id'], attempt.id)
        self.assertIn(f'/assessments/mcq/{attempt.id}/', response.data['attempt']['resume_url'])

    # 10. Admin analytics CSV export authorized
    def test_admin_analytics_csv_export_authorized(self):
        # Create completed attempt with result
        attempt = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            max_score=10,
            total_score=10.0,
            time_limit_seconds=600,
            submitted_at=timezone.now()
        )
        AssessmentResult.objects.create(
            attempt=attempt,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.get('/api/admin/analytics/export/?format=csv')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        content = response.content.decode('utf-8')
        self.assertIn('Attempt ID,Student Username,Email', content)
        self.assertIn(self.alice.username, content)
        self.assertIn('100.0%', content)

    # 11. Admin analytics CSV export student denied and unauthenticated denied
    def test_admin_analytics_csv_export_student_denied(self):
        # Student denied with 403
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.alice_token}')
        response = self.client.get('/api/admin/analytics/export/?format=csv')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Unauthenticated denied with 401
        self.client.credentials()
        response_anon = self.client.get('/api/admin/analytics/export/?format=csv')
        self.assertEqual(response_anon.status_code, status.HTTP_401_UNAUTHORIZED)

    # 12. Custom error handlers render branded HTML
    def test_custom_error_handlers(self):
        request = self.factory.get('/some-path/')

        # 404
        resp_404 = custom_404_view(request)
        self.assertEqual(resp_404.status_code, 404)
        self.assertIn(b'404', resp_404.content)
        self.assertIn(b'Page Not Found', resp_404.content)

        # 403
        resp_403 = custom_403_view(request)
        self.assertEqual(resp_403.status_code, 403)
        self.assertIn(b'403', resp_403.content)
        self.assertIn(b'Access Denied', resp_403.content)

        # 500
        resp_500 = custom_500_view(request)
        self.assertEqual(resp_500.status_code, 500)
        self.assertIn(b'500', resp_500.content)
        self.assertIn(b'Server Error', resp_500.content)

