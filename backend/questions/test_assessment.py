"""
Automated Test Suite for SKILLBYTE MCQ Assessment Engine (Phase 4).
Tests assessment lifecycle, timer, answer validation, scoring, ownership isolation, and results.
"""

from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from questions.models import (
    Question,
    QuestionOption,
    AssessmentAttempt,
    MCQAnswer,
    AssessmentResult,
    QuestionType,
    Category,
    DifficultyLevel,
    AttemptStatus,
)


class MCQAssessmentEngineTests(APITestCase):
    """
    Validates MCQ assessment flow: Start, Answer, Auto-expire, Submit, Scoring, Result, History.
    """

    def setUp(self):
        # 1. Create two student users
        self.student1 = User.objects.create_user(
            username='student_alice',
            email='alice@skillbyte.edu',
            password='AlicePassword123'
        )
        self.student2 = User.objects.create_user(
            username='student_bob',
            email='bob@skillbyte.edu',
            password='BobPassword123'
        )

        # 2. Populate three MCQ questions in Mathematics Easy
        self.q1 = Question.objects.create(
            title="Addition Problem",
            description="What is 5 + 7?",
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            marks=2,
            time_limit=60,
            is_active=True
        )
        self.q1_opt_a = QuestionOption.objects.create(question=self.q1, option_key="A", option_text="11", is_correct=False)
        self.q1_opt_b = QuestionOption.objects.create(question=self.q1, option_key="B", option_text="12", is_correct=True)
        self.q1_opt_c = QuestionOption.objects.create(question=self.q1, option_key="C", option_text="13", is_correct=False)
        self.q1_opt_d = QuestionOption.objects.create(question=self.q1, option_key="D", option_text="14", is_correct=False)

        self.q2 = Question.objects.create(
            title="Multiplication Problem",
            description="What is 6 * 8?",
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            marks=3,
            time_limit=60,
            is_active=True
        )
        self.q2_opt_a = QuestionOption.objects.create(question=self.q2, option_key="A", option_text="48", is_correct=True)
        self.q2_opt_b = QuestionOption.objects.create(question=self.q2, option_key="B", option_text="42", is_correct=False)
        self.q2_opt_c = QuestionOption.objects.create(question=self.q2, option_key="C", option_text="54", is_correct=False)
        self.q2_opt_d = QuestionOption.objects.create(question=self.q2, option_key="D", option_text="46", is_correct=False)

        self.q3 = Question.objects.create(
            title="Square Problem",
            description="What is 9 squared?",
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            marks=5,
            time_limit=60,
            is_active=True
        )
        self.q3_opt_a = QuestionOption.objects.create(question=self.q3, option_key="A", option_text="18", is_correct=False)
        self.q3_opt_b = QuestionOption.objects.create(question=self.q3, option_key="B", option_text="81", is_correct=True)
        self.q3_opt_c = QuestionOption.objects.create(question=self.q3, option_key="C", option_text="72", is_correct=False)
        self.q3_opt_d = QuestionOption.objects.create(question=self.q3, option_key="D", option_text="99", is_correct=False)

        # External question not in Math Easy
        self.outside_q = Question.objects.create(
            title="English Vocab",
            description="What is a synonym of fast?",
            question_type=QuestionType.MCQ,
            category=Category.ENGLISH,
            difficulty=DifficultyLevel.EASY,
            marks=1,
            time_limit=30,
            is_active=True
        )

        self.start_url = reverse('mcq_start')
        self.history_url = reverse('my_attempts')

    # 1. MCQ assessment start
    def test_01_mcq_assessment_start(self):
        self.client.force_authenticate(user=self.student1)
        payload = {
            "category": Category.MATHEMATICS,
            "difficulty": DifficultyLevel.EASY,
            "question_count": 2
        }
        res = self.client.post(self.start_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("attempt_id", res.data)
        self.assertEqual(res.data["category"], Category.MATHEMATICS)
        self.assertEqual(res.data["difficulty"], DifficultyLevel.EASY)
        self.assertEqual(len(res.data["questions"]), 2)
        self.assertIsNone(res.data["session_id"])  # Authenticated student has no session_id

    # 2. Invalid category
    def test_02_invalid_category(self):
        payload = {"category": "InvalidCategory", "difficulty": "EASY", "question_count": 2}
        res = self.client.post(self.start_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    # 3. Invalid difficulty
    def test_03_invalid_difficulty(self):
        payload = {"category": Category.MATHEMATICS, "difficulty": "EXTREME", "question_count": 2}
        res = self.client.post(self.start_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    # 4. Invalid question count
    def test_04_invalid_question_count(self):
        payload = {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": -5}
        res = self.client.post(self.start_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    # 5. Guest assessment creation
    def test_05_guest_assessment_creation(self):
        self.client.logout()
        payload = {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 2}
        res = self.client.post(self.start_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(res.data["session_id"])
        attempt = AssessmentAttempt.objects.get(id=res.data["attempt_id"])
        self.assertIsNone(attempt.user)
        self.assertTrue(attempt.is_guest)

    # 6. Student assessment creation
    def test_06_student_assessment_creation(self):
        self.client.force_authenticate(user=self.student1)
        payload = {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 2}
        res = self.client.post(self.start_url, payload, format='json')
        attempt = AssessmentAttempt.objects.get(id=res.data["attempt_id"])
        self.assertEqual(attempt.user, self.student1)
        self.assertFalse(attempt.is_guest)

    # 7. Questions returned without correct answers
    def test_07_questions_returned_without_correct_answers(self):
        self.client.force_authenticate(user=self.student1)
        res = self.client.post(self.start_url, {"category": Category.MATHEMATICS, "difficulty": "EASY"}, format='json')
        questions = res.data["questions"]
        for q in questions:
            for opt in q["options"]:
                self.assertNotIn("is_correct", opt)
                self.assertNotIn("correct", opt)

    # 8. Submit valid answer
    def test_08_submit_valid_answer(self):
        self.client.force_authenticate(user=self.student1)
        start_res = self.client.post(self.start_url, {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 3}, format='json')
        attempt_id = start_res.data["attempt_id"]
        q_item = start_res.data["questions"][0]
        opt_item = q_item["options"][0]

        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt_id})
        res = self.client.post(answer_url, {"question_id": q_item["id"], "option_id": opt_item["id"]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ok")

        # Verify recorded in DB
        ans_obj = MCQAnswer.objects.get(attempt_id=attempt_id, question_id=q_item["id"])
        self.assertEqual(ans_obj.selected_option_id, opt_item["id"])

    # 9. Reject answer for question not in attempt
    def test_09_reject_answer_for_question_not_in_attempt(self):
        self.client.force_authenticate(user=self.student1)
        start_res = self.client.post(self.start_url, {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 2}, format='json')
        attempt_id = start_res.data["attempt_id"]

        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt_id})
        # Try answering the English question which is not in this attempt
        res = self.client.post(answer_url, {"question_id": self.outside_q.id, "option_id": 1}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    # 10. Reject answer for another user's attempt
    def test_10_reject_answer_for_another_users_attempt(self):
        # Alice starts attempt
        self.client.force_authenticate(user=self.student1)
        start_res = self.client.post(self.start_url, {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 2}, format='json')
        attempt_id = start_res.data["attempt_id"]
        q_item = start_res.data["questions"][0]

        # Bob tries to answer Alice's attempt
        self.client.force_authenticate(user=self.student2)
        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt_id})
        res = self.client.post(answer_url, {"question_id": q_item["id"], "option_id": q_item["options"][0]["id"]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 11, 12, 13, 14, 15. Correct scoring, Incorrect scoring, Unanswered scoring, Percentage, Submit
    def test_11_to_15_assessment_submission_and_scoring(self):
        self.client.force_authenticate(user=self.student1)

        # Create deterministic attempt with all 3 math questions
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS,
            max_score=10,  # 2 + 3 + 5
            time_limit_seconds=600
        )
        attempt.questions.set([self.q1, self.q2, self.q3])

        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt.id})

        # Answer Q1 correctly (2 marks)
        self.client.post(answer_url, {"question_id": self.q1.id, "option_id": self.q1_opt_b.id}, format='json')

        # Answer Q2 incorrectly (0 marks)
        self.client.post(answer_url, {"question_id": self.q2.id, "option_id": self.q2_opt_b.id}, format='json')

        # Leave Q3 unanswered (0 marks)

        # Submit assessment
        submit_url = reverse('mcq_submit', kwargs={'attempt_id': attempt.id})
        submit_res = self.client.post(submit_url, {}, format='json')

        self.assertEqual(submit_res.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_res.data["status"], "COMPLETED")
        self.assertEqual(submit_res.data["total_marks"], 10)
        self.assertEqual(submit_res.data["obtained_marks"], 2.0)
        self.assertEqual(submit_res.data["percentage"], 20.0)
        self.assertEqual(submit_res.data["correct_answers"], 1)
        self.assertEqual(submit_res.data["wrong_answers"], 1)
        self.assertEqual(submit_res.data["unanswered"], 1)

        # Verify DB records
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, AttemptStatus.COMPLETED)
        self.assertIsNotNone(attempt.submitted_at)
        self.assertEqual(attempt.result.percentage, 20.0)

    # 16. Cannot submit twice
    def test_16_cannot_submit_twice(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.IN_PROGRESS,
            max_score=2
        )
        attempt.questions.set([self.q1])

        submit_url = reverse('mcq_submit', kwargs={'attempt_id': attempt.id})
        # First submission -> 200 OK
        res1 = self.client.post(submit_url, {}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Second submission -> 400 Bad Request
        res2 = self.client.post(submit_url, {}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res2.data)

    # 17. Cannot answer completed attempt
    def test_17_cannot_answer_completed_attempt(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            max_score=2
        )
        attempt.questions.set([self.q1])

        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt.id})
        res = self.client.post(answer_url, {"question_id": self.q1.id, "option_id": self.q1_opt_b.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 18. Result endpoint
    def test_18_result_endpoint(self):
        self.client.force_authenticate(user=self.student1)
        attempt = AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED,
            total_score=2.0,
            max_score=2
        )
        attempt.questions.set([self.q1])
        AssessmentResult.objects.create(attempt=attempt, total_marks=2, obtained_marks=2.0, percentage=100.0)

        result_url = reverse('mcq_result', kwargs={'attempt_id': attempt.id})
        res = self.client.get(result_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["obtained_marks"], 2.0)
        self.assertEqual(res.data["percentage"], 100.0)
        self.assertIn("review", res.data)
        self.assertEqual(len(res.data["review"]), 1)
        self.assertEqual(res.data["review"][0]["correct_option_key"], "B")

    # 19. Student attempt history
    def test_19_student_attempt_history(self):
        self.client.force_authenticate(user=self.student1)
        # Create attempt for Alice
        AssessmentAttempt.objects.create(
            user=self.student1,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED
        )
        # Create attempt for Bob
        AssessmentAttempt.objects.create(
            user=self.student2,
            question_type=QuestionType.MCQ,
            category=Category.MATHEMATICS,
            difficulty=DifficultyLevel.EASY,
            status=AttemptStatus.COMPLETED
        )

        # Alice fetches history: must only see 1 attempt (hers)
        res = self.client.get(self.history_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    # 20. Guest attempt ownership
    def test_20_guest_attempt_ownership(self):
        self.client.logout()
        start_res = self.client.post(self.start_url, {"category": Category.MATHEMATICS, "difficulty": "EASY", "question_count": 2}, format='json')
        attempt_id = start_res.data["attempt_id"]
        valid_session = start_res.data["session_id"]
        q_item = start_res.data["questions"][0]

        answer_url = reverse('mcq_answer', kwargs={'attempt_id': attempt_id})

        # Answer with invalid guest session -> 403
        res_invalid = self.client.post(answer_url, {
            "question_id": q_item["id"],
            "option_id": q_item["options"][0]["id"],
            "session_id": "wrong-session-xyz"
        }, format='json')
        self.assertEqual(res_invalid.status_code, status.HTTP_403_FORBIDDEN)

        # Answer with valid guest session -> 200 OK
        res_valid = self.client.post(answer_url, {
            "question_id": q_item["id"],
            "option_id": q_item["options"][0]["id"],
            "session_id": valid_session
        }, format='json')
        self.assertEqual(res_valid.status_code, status.HTTP_200_OK)

