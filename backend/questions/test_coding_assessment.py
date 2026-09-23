"""
Automated Test Suite for SKILLBYTE Live Coding Assessment Module (Phase 5).
Validates workspace setup, client validation, Monaco starter code, server-authoritative timer,
sanitized testcases (no hidden cases leaked), PENDING submission persistence, and access control.
"""

from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from questions.models import (
    Question,
    TestCase,
    AssessmentAttempt,
    CodingSubmission,
    AssessmentResult,
    QuestionType,
    Category,
    DifficultyLevel,
    AttemptStatus,
    SubmissionStatus,
)


class CodingAssessmentModuleTests(APITestCase):
    """
    Validates Phase 5 Live Coding Assessment flow:
    Start -> Workspace details -> Monaco Starter Code -> Client Validation ->
    PENDING Submission -> Result Review -> Multi-Attempt History.
    """

    def setUp(self):
        # 1. Create two test student users
        self.student1 = User.objects.create_user(
            username='coding_alice',
            email='alice@skillbyte.edu',
            password='Password123'
        )
        self.student2 = User.objects.create_user(
            username='coding_bob',
            email='bob@skillbyte.edu',
            password='Password123'
        )

        # 2. Create Coding Problems with Sample and Hidden Test Cases
        self.python_question = Question.objects.create(
            title="Sum of Two Numbers",
            description="Read two integers from stdin and print their sum.",
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            time_limit=2,
            memory_limit=128,
            input_format="Two space-separated integers",
            output_format="Single integer",
            constraints="-10^9 <= a, b <= 10^9",
            sample_input="3 5",
            sample_output="8",
            starter_code={
                "python": "a, b = map(int, input().split())\nprint(a + b)\n",
                "java": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(a + b);\n    }\n}\n",
                "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n    long long a, b;\n    if (cin >> a >> b) cout << a + b << endl;\n    return 0;\n}\n"
            },
            is_active=True
        )

        # Sample test case (visible)
        self.sample_tc = TestCase.objects.create(
            question=self.python_question,
            input_data="3 5",
            expected_output="8",
            is_hidden=False,
            marks=4
        )

        # Hidden test case (NEVER exposed to client)
        self.hidden_tc1 = TestCase.objects.create(
            question=self.python_question,
            input_data="100 250",
            expected_output="350",
            is_hidden=True,
            marks=3
        )
        self.hidden_tc2 = TestCase.objects.create(
            question=self.python_question,
            input_data="-10 25",
            expected_output="15",
            is_hidden=True,
            marks=3
        )

        # Java Coding Problem
        self.java_question = Question.objects.create(
            title="Palindrome String",
            description="Given a string S, print YES if it is a palindrome, or NO otherwise.",
            question_type=QuestionType.CODE,
            category=Category.JAVA,
            difficulty=DifficultyLevel.MEDIUM,
            marks=15,
            time_limit=2,
            memory_limit=256,
            starter_code={"java": "// Java starter code"},
            is_active=True
        )

    # 1. Start coding attempt as student
    def test_01_start_coding_attempt_as_student(self):
        self.client.force_authenticate(user=self.student1)
        url = reverse('coding_start')
        payload = {
            'question_id': self.python_question.id,
            'language': 'python',
            'time_limit_seconds': 1800
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('attempt_id', data)
        self.assertEqual(data['language'], 'python')
        self.assertIsNone(data['session_id'])  # Null for authenticated students
        self.assertEqual(data['question']['id'], self.python_question.id)
        self.assertEqual(data['question']['title'], "Sum of Two Numbers")
        self.assertIn('starter_code', data['question'])

    # 2. Start coding attempt as guest
    def test_02_start_coding_attempt_as_guest(self):
        url = reverse('coding_start')
        payload = {
            'question_id': self.python_question.id,
            'language': 'python',
            'session_id': 'guest-session-coding-123'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIsNotNone(data['session_id'])
        self.assertEqual(data['session_id'], 'guest-session-coding-123')

        attempt = AssessmentAttempt.objects.get(id=data['attempt_id'])
        self.assertTrue(attempt.is_guest)

    # 3. Reject invalid language on start
    def test_03_reject_invalid_language_on_start(self):
        url = reverse('coding_start')
        payload = {
            'question_id': self.python_question.id,
            'language': 'ruby'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid language 'ruby'", response.json()['error'])

    # 4. Filter question by category and difficulty
    def test_04_filter_question_by_category_and_difficulty(self):
        url = reverse('coding_start')
        payload = {
            'category': 'Java',
            'difficulty': 'MEDIUM',
            'language': 'java'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['question']['id'], self.java_question.id)
        self.assertEqual(data['question']['category'], 'Java')

    # 5. Fetch coding attempt details with remaining time
    def test_05_fetch_coding_attempt_detail(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800,
            max_score=10
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_detail', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['attempt_id'], attempt.id)
        self.assertEqual(data['status'], AttemptStatus.IN_PROGRESS)
        self.assertGreater(data['remaining_seconds'], 1700)
        self.assertFalse(data['is_time_expired'])
        self.assertEqual(data['question']['title'], "Sum of Two Numbers")

    # 6. Hidden test cases are NEVER exposed in attempt details
    def test_06_hidden_testcases_never_exposed_in_attempt_details(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_detail', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        data = response.json()
        sample_cases = data['question']['sample_test_cases']

        # Only 1 sample testcase should be present
        self.assertEqual(len(sample_cases), 1)
        self.assertEqual(sample_cases[0]['input_data'], "3 5")

        # Hidden cases must not appear anywhere in payload
        raw_text = str(data)
        self.assertNotIn("100 250", raw_text)
        self.assertNotIn("350", raw_text)
        self.assertNotIn("-10 25", raw_text)

    # 7. Hidden test cases are NEVER exposed in start response
    def test_07_hidden_testcases_never_exposed_in_start_response(self):
        url = reverse('coding_start')
        response = self.client.post(url, {'question_id': self.python_question.id, 'language': 'python'}, format='json')
        data = response.json()
        sample_cases = data['question']['sample_test_cases']

        self.assertEqual(len(sample_cases), 1)
        raw_text = str(data)
        self.assertNotIn("100 250", raw_text)
        self.assertNotIn("350", raw_text)

    # 8. Submit code with valid source code produces PENDING status
    def test_08_submit_code_produces_pending_status(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800,
            max_score=10
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        code_body = "a, b = map(int, input().split())\nprint(a + b)\n"
        response = self.client.post(url, {'source_code': code_body, 'language': 'python'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], SubmissionStatus.PENDING)
        self.assertIn("Phase 6", data['message'])
        self.assertIn('submission_id', data)

    # 9. Verify CodingSubmission is created in database with PENDING status
    def test_09_database_coding_submission_persisted(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        code_body = "print('testing code persistence')"
        self.client.post(url, {'source_code': code_body, 'language': 'python'}, format='json')

        submission = CodingSubmission.objects.filter(attempt=attempt).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.status, SubmissionStatus.PENDING)
        self.assertEqual(submission.source_code, code_body)
        self.assertEqual(submission.language, 'python')
        self.assertEqual(submission.user, self.student1)
        self.assertEqual(submission.total_test_cases, 3)

    # 10. Attempt status transitions to COMPLETED upon submission
    def test_10_attempt_status_completed_on_submission(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        self.client.post(url, {'source_code': "print(1)"}, format='json')

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, AttemptStatus.COMPLETED)
        self.assertIsNotNone(attempt.submitted_at)

    # 11. Reject submission with empty source code
    def test_11_reject_empty_source_code(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {'source_code': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Source code cannot be empty", response.json()['error'])

    # 12. Reject submission with unsupported language
    def test_12_reject_unsupported_language_on_submit(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {'source_code': 'print(1)', 'language': 'rust'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unsupported language 'rust'", response.json()['error'])

    # 13. Reject double submission on already completed attempt
    def test_13_reject_double_submission(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.COMPLETED
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {'source_code': 'print(1)'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already completed", response.json()['error'])

    # 14. Reject submission on expired attempt
    def test_14_reject_submission_on_expired_attempt(self):
        self.client.force_authenticate(user=self.student1)
        # Create attempt with started_at in the past
        past_time = timezone.now() - timedelta(seconds=2000)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800
        )
        AssessmentAttempt.objects.filter(id=attempt.id).update(started_at=past_time)
        attempt.refresh_from_db()
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {'source_code': 'print(1)'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json().get('expired'))

    # 15. Guest can submit with valid session_id
    def test_15_guest_can_submit_with_valid_session(self):
        attempt = AssessmentAttempt.objects.create(
            user=None,
            session_id='guest-session-456',
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS,
            time_limit_seconds=1800
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {
            'source_code': 'print("guest code")',
            'session_id': 'guest-session-456'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], SubmissionStatus.PENDING)

    # 16. Unauthorized guest forbidden to submit
    def test_16_unauthorized_guest_forbidden_to_submit(self):
        attempt = AssessmentAttempt.objects.create(
            user=None,
            session_id='guest-session-456',
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_submit', kwargs={'attempt_id': attempt.id})
        response = self.client.post(url, {
            'source_code': 'print("hack")',
            'session_id': 'wrong-session-999'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 17. Student cannot access another student's attempt
    def test_17_student_cannot_access_another_students_attempt(self):
        # Alice creates attempt
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS
        )
        attempt.questions.add(self.python_question)

        # Bob tries to access Alice's attempt
        self.client.force_authenticate(user=self.student2)
        url = reverse('coding_detail', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 18. Result view shows PENDING submission and execution notice
    def test_18_coding_result_view_shows_pending_and_notice(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.COMPLETED,
            submitted_at=timezone.now()
        )
        attempt.questions.add(self.python_question)
        CodingSubmission.objects.create(
            attempt=attempt,
            user=self.student1,
            question=self.python_question,
            language='python',
            source_code='print(42)',
            status=SubmissionStatus.PENDING,
            total_test_cases=3
        )

        url = reverse('coding_result', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['submission_status'], SubmissionStatus.PENDING)
        self.assertEqual(data['source_code'], 'print(42)')
        self.assertIn("Judge0", data['execution_notice'])
        self.assertIn("Phase 6", data['execution_notice'])

    # 19. Result view rejects attempt that is still in progress
    def test_19_coding_result_rejects_in_progress_attempt(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category=self.python_question.category,
            difficulty=self.python_question.difficulty,
            language='python',
            status=AttemptStatus.IN_PROGRESS
        )
        attempt.questions.add(self.python_question)

        url = reverse('coding_result', kwargs={'attempt_id': attempt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("still in progress", response.json()['error'])

    # 20. My attempts endpoint lists both MCQ and Coding attempts
    def test_20_my_attempts_lists_coding_attempt(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.CODE,
            category='Python',
            difficulty=DifficultyLevel.EASY,
            language='python',
            status=AttemptStatus.COMPLETED,
            total_score=0.0,
            max_score=10
        )
        attempt.questions.add(self.python_question)

        url = reverse('my_attempts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attempts = response.json()
        coding_att = next((a for a in attempts if a['attempt_id'] == attempt.id), None)
        self.assertIsNotNone(coding_att)
        self.assertEqual(coding_att['question_type'], 'CODE')
        self.assertEqual(coding_att['language'], 'python')

