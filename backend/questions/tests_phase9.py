"""
Phase 9 Automated Tests: Admin Question Bank & Test Case Management.
Tests RBAC, MCQ creation & validation, Coding challenge & test cases,
sensitive data leakage protection, toggle active, and deletion integrity.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile, Role
from questions.models import (
    Question, QuestionOption, TestCase as CodingTestCase,
    QuestionType, Category, DifficultyLevel, AssessmentAttempt, AttemptStatus
)


class Phase9AdminQuestionBankTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Admin User
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@skillbyte.test',
            password='Password123!',
            first_name='Admin',
            last_name='Tester'
        )
        self.admin_user.profile.role = Role.ADMIN
        self.admin_user.profile.save()

        # 2. Student User
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@skillbyte.test',
            password='Password123!',
            first_name='Student',
            last_name='Tester'
        )
        # By default signal creates student_user.profile with Role.STUDENT

        # JWT Tokens
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)

    def _auth_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    # --------------------------------------------------------------------------
    # RBAC & Access Control Tests
    # --------------------------------------------------------------------------
    def test_admin_can_access_admin_question_list(self):
        client = self._auth_client(self.admin_token)
        res = client.get('/api/questions/admin/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_student_forbidden_from_admin_endpoints(self):
        client = self._auth_client(self.student_token)
        
        # Admin list
        res = client.get('/api/questions/admin/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # MCQ create
        res = client.post('/api/questions/admin/mcq/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Code create
        res = client.post('/api/questions/admin/code/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_unauthorized(self):
        res = self.client.get('/api/questions/admin/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --------------------------------------------------------------------------
    # MCQ Question Management & Validation
    # --------------------------------------------------------------------------
    def test_admin_create_valid_mcq(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Capital of Japan",
            "description": "What is the capital city of Japan?",
            "category": "General Knowledge",
            "difficulty": "EASY",
            "marks": 2,
            "time_limit": 45,
            "explanation": "Tokyo is the capital of Japan.",
            "is_active": True,
            "options": [
                {"option_key": "A", "option_text": "Tokyo", "is_correct": True},
                {"option_key": "B", "option_text": "Kyoto", "is_correct": False},
                {"option_key": "C", "option_text": "Osaka", "is_correct": False},
                {"option_key": "D", "option_text": "Hiroshima", "is_correct": False},
            ]
        }
        res = client.post('/api/questions/admin/mcq/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertEqual(data['title'], "Capital of Japan")
        self.assertEqual(data['question_type'], "MCQ")
        self.assertEqual(len(data['options']), 4)
        correct_options = [opt for opt in data['options'] if opt['is_correct']]
        self.assertEqual(len(correct_options), 1)
        self.assertEqual(correct_options[0]['option_key'], "A")

    def test_mcq_validation_less_than_two_options(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Invalid MCQ",
            "description": "Too few options",
            "category": "General Knowledge",
            "difficulty": "EASY",
            "marks": 1,
            "time_limit": 60,
            "options": [
                {"option_key": "A", "option_text": "Only one option", "is_correct": True}
            ]
        }
        res = client.post('/api/questions/admin/mcq/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("options", res.json())

    def test_mcq_validation_no_correct_option(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "No Correct Option",
            "description": "All options false",
            "category": "General Knowledge",
            "difficulty": "EASY",
            "marks": 1,
            "time_limit": 60,
            "options": [
                {"option_key": "A", "option_text": "False 1", "is_correct": False},
                {"option_key": "B", "option_text": "False 2", "is_correct": False},
            ]
        }
        res = client.post('/api/questions/admin/mcq/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("options", res.json())

    def test_mcq_validation_multiple_correct_options(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Multiple Correct",
            "description": "More than 1 correct",
            "category": "General Knowledge",
            "difficulty": "EASY",
            "marks": 1,
            "time_limit": 60,
            "options": [
                {"option_key": "A", "option_text": "True 1", "is_correct": True},
                {"option_key": "B", "option_text": "True 2", "is_correct": True},
            ]
        }
        res = client.post('/api/questions/admin/mcq/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mcq_validation_invalid_category(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Invalid Cat",
            "description": "Category not in allowed list",
            "category": "Astrophysics",
            "difficulty": "EASY",
            "marks": 1,
            "time_limit": 60,
            "options": [
                {"option_key": "A", "option_text": "Opt 1", "is_correct": True},
                {"option_key": "B", "option_text": "Opt 2", "is_correct": False},
            ]
        }
        res = client.post('/api/questions/admin/mcq/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_update_mcq(self):
        client = self._auth_client(self.admin_token)
        # Create MCQ
        mcq = Question.objects.create(
            title="Old Title",
            description="Old Desc",
            category="English",
            difficulty="EASY",
            marks=1,
            time_limit=60,
            question_type=QuestionType.MCQ
        )
        QuestionOption.objects.create(question=mcq, option_key="A", option_text="A", is_correct=True)
        QuestionOption.objects.create(question=mcq, option_key="B", option_text="B", is_correct=False)

        update_payload = {
            "title": "Updated English Title",
            "description": "Updated Desc",
            "category": "English",
            "difficulty": "HARD",
            "marks": 5,
            "time_limit": 90,
            "explanation": "Updated explanation",
            "is_active": True,
            "options": [
                {"option_key": "A", "option_text": "New A", "is_correct": False},
                {"option_key": "B", "option_text": "New B", "is_correct": True},
            ]
        }
        res = client.put(f'/api/questions/admin/mcq/{mcq.id}/', update_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mcq.refresh_from_db()
        self.assertEqual(mcq.title, "Updated English Title")
        self.assertEqual(mcq.marks, 5)
        self.assertEqual(mcq.difficulty, "HARD")
        correct_opt = mcq.options.get(is_correct=True)
        self.assertEqual(correct_opt.option_key, "B")
        self.assertEqual(correct_opt.option_text, "New B")

    # --------------------------------------------------------------------------
    # Coding Problem Management & Test Cases
    # --------------------------------------------------------------------------
    def test_admin_create_valid_coding_question(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Sum of Two Numbers",
            "description": "Given two space-separated integers, output their sum.",
            "category": "Python",
            "difficulty": "EASY",
            "marks": 10,
            "time_limit": 2,
            "memory_limit": 128000,
            "starter_code": "import sys\n# write your solution here\n",
            "is_active": True
        }
        res = client.post('/api/questions/admin/code/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertEqual(data['title'], "Sum of Two Numbers")
        self.assertEqual(data['question_type'], "CODE")
        self.assertEqual(data['category'], "Python")

    def test_coding_question_invalid_category(self):
        client = self._auth_client(self.admin_token)
        payload = {
            "title": "Invalid Lang",
            "description": "Rust challenge",
            "category": "Rust",
            "difficulty": "EASY",
            "marks": 10,
            "time_limit": 2,
            "memory_limit": 128000,
        }
        res = client.post('/api/questions/admin/code/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_manage_test_cases_and_security_exposure(self):
        client = self._auth_client(self.admin_token)
        student_client = self._auth_client(self.student_token)

        # 1. Create Coding Problem
        code_q = Question.objects.create(
            title="Multiply Numbers",
            description="Read two ints and multiply them.",
            category="Python",
            difficulty="EASY",
            marks=10,
            time_limit=2,
            memory_limit=128000,
            question_type=QuestionType.CODE
        )

        # 2. Admin adds Sample (Public) Test Case
        sample_tc_res = client.post(
            f'/api/questions/admin/{code_q.id}/test-cases/',
            {
                "input_data": "3 4",
                "expected_output": "12",
                "is_hidden": False,
                "weight": 1.0
            },
            format='json'
        )
        self.assertEqual(sample_tc_res.status_code, status.HTTP_201_CREATED)
        sample_tc_id = sample_tc_res.json()['id']

        # 3. Admin adds Hidden Test Case
        hidden_tc_res = client.post(
            f'/api/questions/admin/{code_q.id}/test-cases/',
            {
                "input_data": "1000 2000",
                "expected_output": "2000000",
                "is_hidden": True,
                "weight": 2.0
            },
            format='json'
        )
        self.assertEqual(hidden_tc_res.status_code, status.HTTP_201_CREATED)
        hidden_tc_id = hidden_tc_res.json()['id']

        # 4. Admin updates the Hidden Test Case
        update_tc_res = client.put(
            f'/api/questions/admin/test-cases/{hidden_tc_id}/',
            {
                "input_data": "500 2",
                "expected_output": "1000",
                "is_hidden": True,
                "weight": 3.0
            },
            format='json'
        )
        self.assertEqual(update_tc_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_tc_res.json()['expected_output'], "1000")

        # 5. SECURITY CHECK: Student viewing question detail should NEVER see hidden test cases
        student_detail_res = student_client.get(f'/api/questions/{code_q.id}/')
        self.assertEqual(student_detail_res.status_code, status.HTTP_200_OK)
        student_data = student_detail_res.json()
        
        # Test cases in student response must contain ONLY sample test cases
        visible_tcs = student_data.get('sample_test_cases', [])
        self.assertEqual(len(visible_tcs), 1)
        self.assertEqual(visible_tcs[0]['input_data'], "3 4")
        self.assertEqual(visible_tcs[0]['expected_output'], "12")
        # Ensure hidden test case is nowhere in the student response
        self.assertNotIn("500 2", str(student_data))
        self.assertNotIn("1000", [tc['expected_output'] for tc in visible_tcs])

        # 6. Admin deletes sample testcase
        del_tc_res = client.delete(f'/api/questions/admin/test-cases/{sample_tc_id}/')
        self.assertEqual(del_tc_res.status_code, status.HTTP_200_OK)
        self.assertEqual(code_q.test_cases.count(), 1)

    # --------------------------------------------------------------------------
    # Toggle Active Status
    # --------------------------------------------------------------------------
    def test_admin_toggle_active_status(self):
        client = self._auth_client(self.admin_token)
        q = Question.objects.create(
            title="Toggle Question",
            description="Test toggle",
            category="English",
            difficulty="EASY",
            marks=1,
            time_limit=60,
            question_type=QuestionType.MCQ,
            is_active=True
        )
        # Toggle to Inactive
        res = client.post(f'/api/questions/admin/{q.id}/toggle-active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.json()['is_active'])
        q.refresh_from_db()
        self.assertFalse(q.is_active)

        # Toggle to Active
        res = client.post(f'/api/questions/admin/{q.id}/toggle-active/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.json()['is_active'])
        q.refresh_from_db()
        self.assertTrue(q.is_active)

    # --------------------------------------------------------------------------
    # Deletion Safety & Integrity
    # --------------------------------------------------------------------------
    def test_safe_delete_unreferenced_question(self):
        client = self._auth_client(self.admin_token)
        q = Question.objects.create(
            title="Unreferenced Question",
            description="Has no attempts",
            category="English",
            difficulty="EASY",
            marks=1,
            time_limit=60,
            question_type=QuestionType.MCQ
        )
        res = client.delete(f'/api/questions/admin/{q.id}/delete/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Question.objects.filter(id=q.id).exists())

    def test_blocked_delete_referenced_question(self):
        client = self._auth_client(self.admin_token)
        q = Question.objects.create(
            title="Referenced Question",
            description="Has attempts",
            category="English",
            difficulty="EASY",
            marks=1,
            time_limit=60,
            question_type=QuestionType.MCQ
        )
        # Create an attempt referencing this question
        attempt = AssessmentAttempt.objects.create(
            user=self.student_user,
            question_type=QuestionType.MCQ,
            category="English",
            status=AttemptStatus.COMPLETED
        )
        attempt.questions.add(q)


        res = client.delete(f'/api/questions/admin/{q.id}/delete/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        data = res.json()
        self.assertTrue(data.get('can_deactivate'))
        self.assertIn("Cannot delete question", data.get('detail', ''))
        # Ensure question was NOT deleted
        self.assertTrue(Question.objects.filter(id=q.id).exists())
