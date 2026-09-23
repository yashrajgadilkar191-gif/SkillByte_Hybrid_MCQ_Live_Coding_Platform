"""
Phase 10 Automated Tests: Leaderboard, Unified Scoring, Admin Analytics, and Live Run Code.
Verifies:
1. Public & authenticated Leaderboard access, ranking calculations with Best-Score deduplication,
   category filtering, and exclusion of admin accounts from student rankings.
2. Unified Scoring service, category mastery percentage formula, skill tier calculations,
   and Progress API integration.
3. Admin Analytics access control (401 guest, 403 student, 200 admin), completion metrics,
   verdict distributions, category performance, and hardest questions.
4. Live Run Code sandbox execution against sample test cases exclusively, ensuring no
   hidden test cases are evaluated or exposed, and attempt status/scores are not modified.
"""

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile, Role
from questions.models import (
    Question, TestCase as CodingTestCase,
    QuestionType, Category, DifficultyLevel,
    AssessmentAttempt, AssessmentResult, AttemptStatus,
    CodingSubmission, SubmissionStatus
)
from questions.scoring_service import (
    compute_student_progress_and_mastery,
    get_skill_tier
)


class Phase10LeaderboardAndScoringTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Admin user
        self.admin = User.objects.create_user(
            username='admin_lead',
            email='admin@skillbyte.test',
            password='Password123!'
        )
        self.admin.profile.role = Role.ADMIN
        self.admin.profile.save()

        # Student 1 (Alice)
        self.alice = User.objects.create_user(
            username='alice_student',
            email='alice@skillbyte.test',
            password='Password123!',
            first_name='Alice'
        )

        # Student 2 (Bob)
        self.bob = User.objects.create_user(
            username='bob_student',
            email='bob@skillbyte.test',
            password='Password123!',
            first_name='Bob'
        )

        self.alice_token = str(RefreshToken.for_user(self.alice).access_token)
        self.bob_token = str(RefreshToken.for_user(self.bob).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

        # Create Questions
        self.q_python = Question.objects.create(
            title='Python Basics',
            description='Test python variables',
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            is_active=True
        )

        self.q_dsa = Question.objects.create(
            title='Two Sum Problem',
            description='Find pairs summing to target',
            question_type=QuestionType.CODE,
            category=Category.DSA,
            difficulty=DifficultyLevel.MEDIUM,
            marks=20,
            is_active=True
        )

    def _auth_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_leaderboard_public_access(self):
        """Guests can view leaderboard rankings without authentication; current_user_rank is null."""
        res = self.client.get('/api/leaderboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('leaderboard', res.data)
        self.assertIsNone(res.data.get('current_user_rank'))

    def test_leaderboard_best_score_per_unique_question_deduplication(self):
        """
        Multiple completed attempts by Alice on the same question take the highest score,
        not the sum of scores.
        """
        # Attempt 1: Alice scores 4 marks on Python Basics (out of 10)
        att1 = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att1.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att1,
            total_marks=10,
            obtained_marks=4.0,
            percentage=40.0
        )

        # Attempt 2: Alice retakes Python Basics and scores 10 marks (out of 10)
        att2 = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att2.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att2,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        # Bob attempts DSA: scores 15 marks
        att3 = AssessmentAttempt.objects.create(
            user=self.bob,
            question_type=QuestionType.CODE,
            category=Category.DSA,
            status=AttemptStatus.COMPLETED
        )
        att3.questions.add(self.q_dsa)
        AssessmentResult.objects.create(
            attempt=att3,
            total_marks=20,
            obtained_marks=15.0,
            percentage=75.0
        )

        # Check Alice's score in scoring service directly
        progress = compute_student_progress_and_mastery(self.alice)
        # Alice should have 10, NOT 14 (4 + 10)
        self.assertEqual(progress['theory_score'], 10.0)
        self.assertEqual(progress['unified_score'], 10.0)

        # Leaderboard API call
        res = self.client.get('/api/leaderboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        lb = res.data['leaderboard']

        # Bob has 15 (Rank 1), Alice has 10 (Rank 2)
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[0]['username'], 'bob_student')
        self.assertEqual(lb[0]['unified_score'], 15.0)
        self.assertEqual(lb[0]['rank'], 1)

        self.assertEqual(lb[1]['username'], 'alice_student')
        self.assertEqual(lb[1]['unified_score'], 10.0)
        self.assertEqual(lb[1]['rank'], 2)

    def test_leaderboard_authenticated_student_receives_current_user_rank(self):
        """Authenticated student receives their personal current_user_rank."""
        att = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        client = self._auth_client(self.alice_token)
        res = client.get('/api/leaderboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data.get('current_user_rank'))
        self.assertEqual(res.data['current_user_rank']['rank'], 1)
        self.assertEqual(res.data['current_user_rank']['unified_score'], 10.0)

    def test_leaderboard_admin_excluded_from_student_rankings(self):
        """Admin users are excluded from the student leaderboard rankings."""
        att = AssessmentAttempt.objects.create(
            user=self.admin,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        res = self.client.get('/api/leaderboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = [x['username'] for x in res.data['leaderboard']]
        self.assertNotIn('admin_lead', usernames)

    def test_leaderboard_category_filtering(self):
        """Filtering by category only aggregates questions belonging to that category."""
        # Alice completed Python (10 pts) and DSA (20 pts)
        att1 = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att1.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att1,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        att2 = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.CODE,
            category=Category.DSA,
            status=AttemptStatus.COMPLETED
        )
        att2.questions.add(self.q_dsa)
        AssessmentResult.objects.create(
            attempt=att2,
            total_marks=20,
            obtained_marks=20.0,
            percentage=100.0
        )

        # Filter by Python
        res = self.client.get('/api/leaderboard/?category=Python')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['leaderboard']), 1)
        self.assertEqual(res.data['leaderboard'][0]['unified_score'], 10.0)
        self.assertEqual(res.data['leaderboard'][0]['theory_score'], 10.0)
        self.assertEqual(res.data['leaderboard'][0]['coding_score'], 0.0)

    def test_category_mastery_formula(self):
        """
        Category Mastery % = SUM(best obtained_marks in category) / SUM(max marks for those questions) * 100.
        """
        # Question Python 1: 10 marks. Alice gets 5 marks.
        att1 = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att1.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att1,
            total_marks=10,
            obtained_marks=5.0,
            percentage=50.0
        )

        progress = compute_student_progress_and_mastery(self.alice)
        py_mastery = next((c for c in progress['category_mastery'] if c['category'] == 'Python'), None)
        self.assertIsNotNone(py_mastery)
        self.assertEqual(py_mastery['best_obtained_marks'], 5.0)
        self.assertEqual(py_mastery['max_available_marks'], 10.0)
        self.assertEqual(py_mastery['mastery_percentage'], 50.0)

    def test_skill_tier_thresholds(self):
        """Skill tier calculation thresholds: Novice, Apprentice, Specialist, Master."""
        tier, _ = get_skill_tier(10.0)
        self.assertEqual(tier, 'Novice')
        tier, _ = get_skill_tier(60.0)
        self.assertEqual(tier, 'Apprentice')
        tier, _ = get_skill_tier(180.0)
        self.assertEqual(tier, 'Specialist')
        tier, _ = get_skill_tier(350.0)
        self.assertEqual(tier, 'Master')

    def test_my_progress_api_returns_unified_metrics(self):
        """GET /api/assessments/my-progress/ returns unified score and tier."""
        att = AssessmentAttempt.objects.create(
            user=self.alice,
            question_type=QuestionType.MCQ,
            category=Category.PYTHON,
            status=AttemptStatus.COMPLETED
        )
        att.questions.add(self.q_python)
        AssessmentResult.objects.create(
            attempt=att,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        client = self._auth_client(self.alice_token)
        res = client.get('/api/assessments/my-progress/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('unified_score', res.data)
        self.assertIn('theory_score', res.data)
        self.assertIn('coding_score', res.data)
        self.assertIn('skill_tier', res.data)
        self.assertIn('category_mastery', res.data)
        self.assertEqual(res.data['unified_score'], 10.0)


class Phase10AdminAnalyticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='admin_an',
            email='admin_an@skillbyte.test',
            password='Password123!'
        )
        self.admin.profile.role = Role.ADMIN
        self.admin.profile.save()

        self.student = User.objects.create_user(
            username='student_an',
            email='student_an@skillbyte.test',
            password='Password123!'
        )

        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)
        self.student_token = str(RefreshToken.for_user(self.student).access_token)

    def _auth_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_admin_analytics_access_denied_for_unauthenticated_and_student(self):
        """Guests receive 401, students receive 403."""
        # Unauthenticated
        res = self.client.get('/api/admin/analytics/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Student
        client = self._auth_client(self.student_token)
        res = client.get('/api/admin/analytics/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_analytics_accessible_by_admin(self):
        """Admin user receives 200 with full metrics payload."""
        client = self._auth_client(self.admin_token)
        res = client.get('/api/admin/analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('users', res.data)
        self.assertIn('attempts', res.data)
        self.assertIn('scoring', res.data)
        self.assertIn('coding_verdicts', res.data)
        self.assertIn('categories', res.data)
        self.assertIn('hardest_questions', res.data)

        self.assertEqual(res.data['users']['total_students'], 1)


class Phase10LiveRunCodeTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.student = User.objects.create_user(
            username='student_runner',
            email='runner@skillbyte.test',
            password='Password123!'
        )
        self.token = str(RefreshToken.for_user(self.student).access_token)

        self.coding_q = Question.objects.create(
            title='Sum of Two Integers',
            description='Compute a + b',
            question_type=QuestionType.CODE,
            category=Category.DSA,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            is_active=True
        )

        # Sample Test Case (public)
        self.sample_tc = CodingTestCase.objects.create(
            question=self.coding_q,
            input_data='2 3\n',
            expected_output='5\n',
            is_hidden=False,
            marks=5
        )

        # Hidden Test Case (MUST NOT BE RUN OR LEAKED)
        self.hidden_tc = CodingTestCase.objects.create(
            question=self.coding_q,
            input_data='100 200\n',
            expected_output='300\n',
            is_hidden=True,
            marks=5
        )

        self.attempt = AssessmentAttempt.objects.create(
            user=self.student,
            question_type=QuestionType.CODE,
            category=Category.DSA,
            status=AttemptStatus.IN_PROGRESS
        )
        self.attempt.questions.add(self.coding_q)

    def _auth_client(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        return client

    @patch('questions.assessment_views.Judge0Service.execute_test_case')
    def test_run_code_executes_only_sample_test_cases(self, mock_exec):
        """Run code executes strictly against sample test cases and never against hidden ones."""
        mock_exec.return_value = {
            'stdout': '5\n',
            'stderr': None,
            'compile_output': None,
            'time': '0.045',
            'memory': 4200,
            'status_id': 3,
            'status_description': 'Accepted'
        }

        client = self._auth_client()
        payload = {
            'source_code': 'print(sum(map(int, input().split())))',
            'language': 'python'
        }

        res = client.post(f'/api/assessments/coding/{self.attempt.id}/run/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify only 1 test case was executed (the sample one)
        self.assertEqual(mock_exec.call_count, 1)
        self.assertEqual(res.data['total_sample_cases'], 1)
        self.assertEqual(len(res.data['test_cases']), 1)
        self.assertEqual(res.data['test_cases'][0]['test_case_number'], 1)
        self.assertTrue(res.data['test_cases'][0]['passed'])

        # Verify hidden test case was NEVER passed
        executed_tc = mock_exec.call_args.kwargs.get('test_case')
        self.assertIsNotNone(executed_tc)
        self.assertEqual(executed_tc.input_data, '2 3\n')
        self.assertFalse(executed_tc.is_hidden)

        # Verify attempt was NOT modified/completed
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, AttemptStatus.IN_PROGRESS)

        # Verify no Submission or AssessmentResult created
        self.assertEqual(CodingSubmission.objects.filter(attempt=self.attempt).count(), 0)
        self.assertEqual(AssessmentResult.objects.filter(attempt=self.attempt).count(), 0)

