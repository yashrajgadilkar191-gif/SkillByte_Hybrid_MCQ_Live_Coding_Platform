"""
Views for SKILLBYTE Question Bank API (Phase 3).
Read-only student-facing endpoints returning sanitized, safe question data.
"""

from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from accounts.permissions import IsAdmin
from .models import Question, QuestionOption, TestCase, QuestionType, Category, DifficultyLevel
from .serializers import (
    QuestionStudentListSerializer,
    QuestionStudentDetailSerializer,
    QuestionAdminListSerializer,
    QuestionAdminDetailSerializer,
    MCQQuestionCreateUpdateSerializer,
    CodingQuestionCreateUpdateSerializer,
    TestCaseAdminSerializer,
    TestCaseCreateUpdateSerializer,
)


class QuestionListView(APIView):
    """
    GET /api/questions/
    Public/Student read-only list of active questions.
    Supports filtering by:
    - type: MCQ or CODE
    - category / subject: e.g. Mathematics, Python, etc.
    - difficulty: EASY, MEDIUM, HARD
    """
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Question.objects.filter(is_active=True)

        # Filters
        q_type = request.query_params.get('type')
        if q_type:
            queryset = queryset.filter(question_type__iexact=q_type)

        category = request.query_params.get('category') or request.query_params.get('subject')
        if category:
            queryset = queryset.filter(category__iexact=category)

        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)

        serializer = QuestionStudentListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuestionDetailView(APIView):
    """
    GET /api/questions/<id>/
    Returns sanitized student-facing details for a single question.
    Never exposes is_correct or hidden test cases.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        question = get_object_or_404(Question, pk=pk, is_active=True)
        serializer = QuestionStudentDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==============================================================================
# PHASE 9: ADMIN QUESTION BANK & TEST CASE MANAGEMENT VIEWS
# Accessible only by users with ADMIN role (or superuser/staff).
# ==============================================================================

class AdminQuestionListView(APIView):
    """
    GET /api/questions/admin/
    Lists questions with administrative metadata (total options, sample/hidden test cases,
    is_active flag, and whether student attempts exist).
    Supports query parameters:
    - type: MCQ or CODE
    - category: string
    - difficulty: EASY, MEDIUM, HARD
    - is_active: true / false
    - search / q: search query across title and description
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = Question.objects.all().order_by('-created_at')

        q_type = request.query_params.get('type')
        if q_type:
            queryset = queryset.filter(question_type__iexact=q_type)

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)

        is_active = request.query_params.get('is_active')
        if is_active is not None and is_active != '':
            if is_active.lower() in ('true', '1'):
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ('false', '0'):
                queryset = queryset.filter(is_active=False)

        search_query = request.query_params.get('search') or request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )

        serializer = QuestionAdminListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminQuestionDetailView(APIView):
    """
    GET /api/questions/admin/<int:pk>/
    DELETE /api/questions/admin/<int:pk>/
    Retrieves full question details for admin editing (including options with correct answers,
    all test cases with sample/hidden flags, input/output).
    DELETE safely deletes if no attempts reference it.
    """
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        serializer = QuestionAdminDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        has_attempts = question.assessment_attempts_set.exists() or question.coding_submissions.exists()
        if has_attempts:
            return Response(
                {
                    "detail": "Cannot delete question because student attempts or submissions reference it. Deactivate the question instead to hide it from new assessments.",
                    "can_deactivate": True,
                    "is_active": question.is_active,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        question.delete()
        return Response({"message": "Question deleted successfully."}, status=status.HTTP_200_OK)


class AdminMCQCreateView(APIView):
    """
    POST /api/questions/admin/mcq/
    Creates a new MCQ question with options.
    Validates category, marks, time_limit, min 2 options, and exactly 1 correct option.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = MCQQuestionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(question).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminMCQUpdateView(APIView):
    """
    PUT/PATCH /api/questions/admin/mcq/<int:pk>/
    Updates an existing MCQ question and its options.
    """
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        question = get_object_or_404(Question, pk=pk, question_type=QuestionType.MCQ)
        serializer = MCQQuestionCreateUpdateSerializer(question, data=request.data, partial=False)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(Question, pk=pk, question_type=QuestionType.MCQ)
        serializer = MCQQuestionCreateUpdateSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminCodingCreateView(APIView):
    """
    POST /api/questions/admin/code/
    Creates a new coding challenge.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = CodingQuestionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(question).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminCodingUpdateView(APIView):
    """
    PUT/PATCH /api/questions/admin/code/<int:pk>/
    Updates an existing coding challenge.
    """
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        question = get_object_or_404(Question, pk=pk, question_type=QuestionType.CODE)
        serializer = CodingQuestionCreateUpdateSerializer(question, data=request.data, partial=False)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(Question, pk=pk, question_type=QuestionType.CODE)
        serializer = CodingQuestionCreateUpdateSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                QuestionAdminDetailSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminQuestionToggleActiveView(APIView):
    """
    POST /api/questions/admin/<int:pk>/toggle-active/
    Toggles the is_active status of a question.
    """
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        question.is_active = not question.is_active
        question.save(update_fields=['is_active'])
        return Response({
            "id": question.id,
            "title": question.title,
            "is_active": question.is_active,
            "message": f"Question '{question.title}' is now {'active' if question.is_active else 'inactive'}."
        }, status=status.HTTP_200_OK)


class AdminQuestionDeleteView(APIView):
    """
    POST /api/questions/admin/<int:pk>/delete/
    DELETE /api/questions/admin/<int:pk>/delete/
    Safely deletes a question or blocks deletion if attempts reference it.
    """
    permission_classes = [IsAdmin]

    def _delete_question(self, question):
        has_attempts = question.assessment_attempts_set.exists() or question.coding_submissions.exists()
        if has_attempts:
            return Response(
                {
                    "detail": "Cannot delete question because student attempts or submissions reference it. Deactivate the question instead to hide it from new assessments.",
                    "can_deactivate": True,
                    "is_active": question.is_active,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        question.delete()
        return Response({"message": "Question deleted successfully."}, status=status.HTTP_200_OK)

    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        return self._delete_question(question)

    def delete(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        return self._delete_question(question)


class AdminTestCaseCreateView(APIView):
    """
    POST /api/questions/admin/<int:question_id>/test-cases/
    Creates a new test case for a coding challenge.
    """
    permission_classes = [IsAdmin]

    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id, question_type=QuestionType.CODE)
        serializer = TestCaseCreateUpdateSerializer(data=request.data, context={'question': question})
        if serializer.is_valid():
            test_case = serializer.save(question=question)
            return Response(
                TestCaseAdminSerializer(test_case).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminTestCaseDetailView(APIView):
    """
    PUT /api/questions/admin/test-cases/<int:pk>/
    PATCH /api/questions/admin/test-cases/<int:pk>/
    DELETE /api/questions/admin/test-cases/<int:pk>/
    Updates or deletes a specific test case.
    """
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        test_case = get_object_or_404(TestCase, pk=pk)
        serializer = TestCaseCreateUpdateSerializer(test_case, data=request.data, partial=False)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                TestCaseAdminSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        test_case = get_object_or_404(TestCase, pk=pk)
        serializer = TestCaseCreateUpdateSerializer(test_case, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(
                TestCaseAdminSerializer(updated).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        test_case = get_object_or_404(TestCase, pk=pk)
        test_case.delete()
        return Response({"message": "Test case deleted successfully."}, status=status.HTTP_200_OK)


