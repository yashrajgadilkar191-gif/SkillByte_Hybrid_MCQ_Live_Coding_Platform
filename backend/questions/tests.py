"""
Automated Test Suite for SKILLBYTE Question Bank & Assessments Foundation (Phase 3).
"""

from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from questions.models import (
    Question,
    QuestionOption,
    TestCase,
    AssessmentAttempt,
    MCQAnswer,
    CodingSubmission,
    AssessmentResult,
    QuestionType,
    Category,
    DifficultyLevel,
    AttemptStatus,
    SubmissionStatus,
)


class QuestionBankModelAndAPITests(APITestCase):
    """
    Validates model integrity, relationships, security sanitation, and API behavior for Phase 3.
    """

    def setUp(self):
        # Create student user
        self.student_user = User.objects.create_user(
            username='test_student',
            email='test_student@skillbyte.edu',
            password='TestPassword123'
        )

        # 1. Create a sample MCQ Question
        self.mcq_question = Question.objects.create(
            title="Capital of India",
            description="What is the capital city of India?",
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            marks=1,
            time_limit=30,
            is_active=True
        )

        self.opt_a = QuestionOption.objects.create(
            question=self.mcq_question,
            option_key="A",
            option_text="Mumbai",
            is_correct=False
        )
        self.opt_b = QuestionOption.objects.create(
            question=self.mcq_question,
            option_key="B",
            option_text="New Delhi",
            is_correct=True
        )
        self.opt_c = QuestionOption.objects.create(
            question=self.mcq_question,
            option_key="C",
            option_text="Kolkata",
            is_correct=False
        )
        self.opt_d = QuestionOption.objects.create(
            question=self.mcq_question,
            option_key="D",
            option_text="Chennai",
            is_correct=False
        )

        # 2. Create a sample Coding Problem
        self.coding_question = Question.objects.create(
            title="Print Hello World",
            description="Write a program to print Hello World.",
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            marks=10,
            time_limit=2,
            memory_limit=128,
            input_format="No input",
            output_format="Hello World",
            starter_code={"python": "print('Hello World')"},
            is_active=True
        )

        self.sample_testcase = TestCase.objects.create(
            question=self.coding_question,
            input_data="",
            expected_output="Hello World",
            is_hidden=False,
            marks=4
        )

        self.hidden_testcase = TestCase.objects.create(
            question=self.coding_question,
            input_data="ignored",
            expected_output="Hello World",
            is_hidden=True,
            marks=6
        )

    # 1. MCQ question creation
    def test_01_mcq_question_creation(self):
        self.assertEqual(self.mcq_question.question_type, QuestionType.MCQ)
        self.assertEqual(self.mcq_question.category, Category.GENERAL_KNOWLEDGE)
        self.assertEqual(self.mcq_question.marks, 1)

    # 2. Coding question creation
    def test_02_coding_question_creation(self):
        self.assertEqual(self.coding_question.question_type, QuestionType.CODE)
        self.assertEqual(self.coding_question.category, Category.PYTHON)
        self.assertEqual(self.coding_question.marks, 10)

    # 3. MCQ options creation
    def test_03_mcq_options_count(self):
        self.assertEqual(self.mcq_question.options.count(), 4)
        option_keys = set(self.mcq_question.options.values_list('option_key', flat=True))
        self.assertEqual(option_keys, {'A', 'B', 'C', 'D'})

    # 4. Correct answer stored in database
    def test_04_correct_answer_stored_in_database(self):
        correct_opts = self.mcq_question.options.filter(is_correct=True)
        self.assertEqual(correct_opts.count(), 1)
        self.assertEqual(correct_opts.first().option_key, 'B')
        self.assertEqual(correct_opts.first().option_text, 'New Delhi')

    # 5. Coding test cases creation
    def test_05_coding_test_cases_creation(self):
        self.assertEqual(self.coding_question.test_cases.count(), 2)
        sample = self.coding_question.test_cases.filter(is_hidden=False).first()
        self.assertEqual(sample.expected_output, "Hello World")

    # 6. Hidden test cases stored correctly
    def test_06_hidden_test_cases_stored_correctly(self):
        hidden = self.coding_question.test_cases.filter(is_hidden=True)
        self.assertEqual(hidden.count(), 1)
        self.assertTrue(hidden.first().is_hidden)

    # 7. Student API does not expose correct MCQ answers
    def test_07_student_api_does_not_expose_correct_mcq_answers(self):
        url = reverse('question_detail', kwargs={'pk': self.mcq_question.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.data.get('options', [])
        self.assertEqual(len(options), 4)
        for opt in options:
            self.assertNotIn('is_correct', opt)
            self.assertNotIn('correct', opt)

    # 8. Student API does not expose hidden test case data
    def test_08_student_api_does_not_expose_hidden_test_case_data(self):
        url = reverse('question_detail', kwargs={'pk': self.coding_question.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sample_test_cases = response.data.get('sample_test_cases', [])
        # Only 1 sample test case should be returned
        self.assertEqual(len(sample_test_cases), 1)
        self.assertEqual(sample_test_cases[0]['id'], self.sample_testcase.id)
        # Ensure hidden test case ID is not in response
        testcase_ids = [tc['id'] for tc in sample_test_cases]
        self.assertNotIn(self.hidden_testcase.id, testcase_ids)

    # 9. Guest attempt can exist
    def test_09_guest_attempt_can_exist(self):
        guest_attempt = AssessmentAttempt.objects.create(
            user=None,
            session_id='guest-session-xyz-123',
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS
        )
        self.assertIsNone(guest_attempt.user)
        self.assertTrue(guest_attempt.is_guest)
        self.assertEqual(guest_attempt.session_id, 'guest-session-xyz-123')

    # 10. Student attempt is associated with user
    def test_10_student_attempt_is_associated_with_user(self):
        student_attempt = AssessmentAttempt.objects.create(
            user=self.student_user,
            question_type=QuestionType.CODE,
            category=Category.PYTHON,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS
        )
        self.assertIsNotNone(student_attempt.user)
        self.assertFalse(student_attempt.is_guest)
        self.assertEqual(student_attempt.user.username, 'test_student')

    # 11. Result relationship
    def test_11_result_relationship(self):
        attempt = AssessmentAttempt.objects.create(
            user=self.student_user,
            question_type=QuestionType.MCQ,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            total_score=1.0,
            max_score=1
        )
        result = AssessmentResult.objects.create(
            attempt=attempt,
            total_marks=1,
            obtained_marks=1.0,
            percentage=100.0
        )
        self.assertEqual(attempt.result, result)
        self.assertEqual(result.percentage, 100.0)

    # 12. Submission relationship
    def test_12_submission_relationship(self):
        submission = CodingSubmission.objects.create(
            user=self.student_user,
            question=self.coding_question,
            language='python',
            source_code="print('Hello World')",
            status=SubmissionStatus.ACCEPTED,
            score=10.0,
            passed_test_cases=2,
            total_test_cases=2
        )
        self.assertEqual(submission.question, self.coding_question)
        self.assertEqual(submission.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(self.coding_question.coding_submissions.count(), 1)

    # 13. Question type validation
    def test_13_question_type_category_validation(self):
        # Category mismatch: General Knowledge cannot be a Coding problem
        invalid_question = Question(
            title="Invalid Pairing",
            description="Testing category validation",
            question_type=QuestionType.CODE,
            category=Category.GENERAL_KNOWLEDGE,
            difficulty=DifficultyLevel.EASY
        )
        with self.assertRaises(ValidationError):
            invalid_question.clean()

    # 14. Difficulty validation
    def test_14_difficulty_choices_validation(self):
        valid_difficulties = {DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD}
        self.assertIn(self.mcq_question.difficulty, valid_difficulties)
        self.assertIn(self.coding_question.difficulty, valid_difficulties)

    # 15. Phase 1 health endpoint still works
    def test_15_phase_1_health_endpoint_still_works(self):
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            "status": "ok",
            "service": "SkillByte API"
        })

    # 16. Questions list filtering works
    def test_16_question_list_filtering(self):
        url = reverse('question_list')

        # Filter by type=MCQ
        res_mcq = self.client.get(url, {'type': 'MCQ'})
        self.assertEqual(res_mcq.status_code, status.HTTP_200_OK)
        for q in res_mcq.data:
            self.assertEqual(q['type'], 'MCQ')

        # Filter by type=CODE
        res_code = self.client.get(url, {'type': 'CODE'})
        self.assertEqual(res_code.status_code, status.HTTP_200_OK)
        for q in res_code.data:
            self.assertEqual(q['type'], 'CODE')

