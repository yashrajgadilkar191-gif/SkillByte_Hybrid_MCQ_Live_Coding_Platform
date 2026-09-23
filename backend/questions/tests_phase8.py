"""
Automated Test Suite for SKILLBYTE Attempt History and Progress Tracking (Phase 8).
Validates attempt listing, filtering, student/guest isolation, progress metrics calculation,
security sanitation (no hidden test cases/tokens), and page view routing.
"""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from questions.models import (
    Question,
    TestCase,
    AssessmentAttempt,
    AssessmentResult,
    CodingSubmission,
    QuestionType,
    Category,
    DifficultyLevel,
    AttemptStatus,
    SubmissionStatus,
)


class Phase8AttemptHistoryAndProgressTests(APITestCase):
    """
    Validates Phase 8 Attempt History and Progress Tracking endpoints and isolation.
    """

    def setUp(self):
        # 1. Create two student users
        self.student_1 = User.objects.create_user(
            username='student_one',
            email='student_one@skillbyte.edu',
            password='Password123!'
        )
        self.student_2 = User.objects.create_user(
            username='student_two',
            email='student_two@skillbyte.edu',
            password='Password123!'
        )

        # 2. Create questions
        self.coding_question = Question.objects.create(
            title="Two Sum Problem",
            description="Find indices of two numbers that add up to target.",
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            time_limit=2.0,
            memory_limit=256,
            is_active=True
        )
        # Add a sample and a hidden test case
        self.sample_case = TestCase.objects.create(
            question=self.coding_question,
            input_data="[2, 7, 11, 15]\n9",
            expected_output="[0, 1]",
            is_hidden=False,
            marks=5
        )
        self.hidden_case = TestCase.objects.create(
            question=self.coding_question,
            input_data="[3, 2, 4]\n6",
            expected_output="[1, 2]",
            is_hidden=True,
            marks=5
        )

        self.mcq_question = Question.objects.create(
            title="General Knowledge Q1",
            description="What is the speed of light?",
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            marks=5,
            is_active=True
        )

        # 3. Create attempts for Student 1: 1 Completed MCQ, 1 Completed Coding, 1 In-Progress Coding
        self.att_mcq_1 = AssessmentAttempt.objects.create(
            user=self.student_1,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            total_score=5.0,
            max_score=5
        )
        AssessmentResult.objects.create(
            attempt=self.att_mcq_1,
            total_marks=5,
            obtained_marks=5.0,
            percentage=100.0
        )

        self.att_code_1 = AssessmentAttempt.objects.create(
            user=self.student_1,
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            language='python',
            status=AttemptStatus.COMPLETED,
            total_score=8.0,
            max_score=10
        )
        self.submission_code_1 = CodingSubmission.objects.create(
            attempt=self.att_code_1,
            user=self.student_1,
            question=self.coding_question,
            language='python',
            source_code='print("solution")',
            judge0_token='dummy_secret_token_123',
            status=SubmissionStatus.ACCEPTED,
            score=8.0,
            passed_test_cases=2,
            total_test_cases=2
        )
        AssessmentResult.objects.create(
            attempt=self.att_code_1,
            total_marks=10,
            obtained_marks=8.0,
            percentage=80.0
        )

        self.att_code_in_progress = AssessmentAttempt.objects.create(
            user=self.student_1,
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.MEDIUM,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            total_score=0.0,
            max_score=10
        )

        # 4. Create attempt for Student 2
        self.att_student_2 = AssessmentAttempt.objects.create(
            user=self.student_2,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.HARD,
            status=AttemptStatus.COMPLETED,
            total_score=10.0,
            max_score=10
        )
        AssessmentResult.objects.create(
            attempt=self.att_student_2,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

        # 5. Create attempts for Guest 1 and Guest 2
        self.guest_session_1 = "guest-session-uuid-111"
        self.guest_session_2 = "guest-session-uuid-222"

        self.att_guest_1 = AssessmentAttempt.objects.create(
            user=None,
            session_id=self.guest_session_1,
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            language='python',
            status=AttemptStatus.COMPLETED,
            total_score=10.0,
            max_score=10
        )
        AssessmentResult.objects.create(
            attempt=self.att_guest_1,
            total_marks=10,
            obtained_marks=10.0,
            percentage=100.0
        )

    def test_student_can_list_own_attempts(self):
        """Authenticated student receives their own attempts."""
        self.client.force_authenticate(user=self.student_1)
        response = self.client.get('/api/assessments/my-attempts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        attempt_ids = [item['attempt_id'] for item in response.data]
        self.assertIn(self.att_mcq_1.id, attempt_ids)
        self.assertIn(self.att_code_1.id, attempt_ids)
        self.assertIn(self.att_code_in_progress.id, attempt_ids)
        # Must NOT contain student 2's attempt
        self.assertNotIn(self.att_student_2.id, attempt_ids)
        # Must NOT contain guest's attempt
        self.assertNotIn(self.att_guest_1.id, attempt_ids)

    def test_student_isolation_guarantee(self):
        """Student 2 cannot see Student 1's attempts."""
        self.client.force_authenticate(user=self.student_2)
        response = self.client.get('/api/assessments/my-attempts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['attempt_id'], self.att_student_2.id)

    def test_filter_by_question_type(self):
        """Filtering by ?type=MCQ and ?type=CODE works accurately."""
        self.client.force_authenticate(user=self.student_1)
        
        # Test MCQ filter
        res_mcq = self.client.get('/api/assessments/my-attempts/?type=MCQ')
        self.assertEqual(res_mcq.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_mcq.data), 1)
        self.assertEqual(res_mcq.data[0]['question_type'], QuestionType.MCQ)

        # Test CODE filter
        res_code = self.client.get('/api/assessments/my-attempts/?type=CODE')
        self.assertEqual(res_code.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_code.data), 2)
        for att in res_code.data:
            self.assertEqual(att['question_type'], QuestionType.CODE)

    def test_filter_by_status(self):
        """Filtering by ?status=COMPLETED works."""
        self.client.force_authenticate(user=self.student_1)
        res = self.client.get('/api/assessments/my-attempts/?status=COMPLETED')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        for att in res.data:
            self.assertEqual(att['status'], AttemptStatus.COMPLETED)

    def test_filter_limit(self):
        """Limit parameter caps the number of attempts returned."""
        self.client.force_authenticate(user=self.student_1)
        res = self.client.get('/api/assessments/my-attempts/?limit=1')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_guest_session_attempt_listing(self):
        """Guests can retrieve attempts matching their session_id."""
        response = self.client.get(f'/api/assessments/my-attempts/?session_id={self.guest_session_1}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['attempt_id'], self.att_guest_1.id)

    def test_guest_session_isolation(self):
        """Guest 2 session cannot see Guest 1 attempts."""
        response = self.client.get(f'/api/assessments/my-attempts/?session_id={self.guest_session_2}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_request_without_session_rejected(self):
        """Unauthenticated request without session_id returns 401."""
        response = self.client.get('/api/assessments/my-attempts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_security_sanitation_no_tokens_or_hidden_cases(self):
        """Zero exposure of Judge0 tokens or hidden test case contents."""
        self.client.force_authenticate(user=self.student_1)
        response = self.client.get('/api/assessments/my-attempts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_content = response.content.decode()
        self.assertNotIn("dummy_secret_token_123", raw_content)
        self.assertNotIn("is_hidden", raw_content)

    def test_progress_metrics_student(self):
        """GET /api/assessments/progress/ returns computed analytics for student."""
        self.client.force_authenticate(user=self.student_1)
        response = self.client.get('/api/assessments/progress/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['total_attempts'], 3)
        self.assertEqual(data['completed_attempts'], 2)
        self.assertEqual(data['in_progress_attempts'], 1)
        self.assertEqual(data['mcq_count'], 1)
        self.assertEqual(data['coding_count'], 2)
        # Completed: 100% and 80% -> average is 90.0%
        self.assertEqual(data['average_percentage'], 90.0)
        self.assertTrue(len(data['category_breakdown']) >= 2)
        self.assertTrue(len(data['recent_attempts']) <= 5)

    def test_progress_metrics_guest(self):
        """GET /api/assessments/progress/?session_id=... returns analytics for guest."""
        response = self.client.get(f'/api/assessments/progress/?session_id={self.guest_session_1}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['total_attempts'], 1)
        self.assertEqual(data['completed_attempts'], 1)
        self.assertEqual(data['average_percentage'], 100.0)

    def test_frontend_attempt_history_page_loads(self):
        """Frontend attempt history page at /attempts/ renders HTTP 200."""
        response = self.client.get('/attempts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Assessment History & Progress")

    def test_frontend_dashboard_page_loads(self):
        """Frontend dashboard page at /dashboard/ renders HTTP 200."""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Progress Overview")

