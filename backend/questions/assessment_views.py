"""
Views for SKILLBYTE MCQ Assessment Engine (Phase 4).
Handles assessment creation, real-time timer tracking, question selection,
answer recording, server-side scoring, result calculation, and history.
"""

import uuid
import requests
from .judge0_service import Judge0Service, LANGUAGE_IDS
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .scoring_service import compute_student_progress_and_mastery

from .models import (
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
from .serializers import (
    QuestionOptionStudentSerializer,
    TestCaseStudentSerializer,
)


def get_attempt_for_request(attempt_id, request):
    """
    Validates attempt existence and ownership.
    Ensures students only access their own attempts, and guests only access
    their own session-identified attempts.
    """
    attempt = get_object_or_404(AssessmentAttempt, id=attempt_id)

    # Student ownership check
    if attempt.user:
        if not (request.user and request.user.is_authenticated and request.user == attempt.user):
            return None, Response(
                {"error": "Forbidden: You do not have permission to access this assessment attempt."},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # Guest ownership check
        client_session_id = (
            request.data.get('session_id') or
            request.query_params.get('session_id') or
            request.headers.get('X-Session-ID')
        )
        if not client_session_id or client_session_id != attempt.session_id:
            return None, Response(
                {"error": "Forbidden: Invalid or missing guest session identifier."},
                status=status.HTTP_403_FORBIDDEN
            )

    return attempt, None


def evaluate_attempt_server_side(attempt):
    """
    Authoritative server-side evaluation for an MCQ AssessmentAttempt.
    """
    questions = attempt.questions.all()
    total_marks = 0
    obtained_marks = 0.0
    correct_count = 0
    answered_count = 0

    for q in questions:
        total_marks += q.marks
        answer = attempt.mcq_answers.filter(question=q).first()

        if answer and answer.selected_option:
            answered_count += 1
            if answer.selected_option.is_correct:
                answer.is_correct = True
                answer.marks_obtained = float(q.marks)
                correct_count += 1
                obtained_marks += float(q.marks)
            else:
                answer.is_correct = False
                answer.marks_obtained = 0.0
            answer.save()
        else:
            # Unanswered question
            if not answer:
                answer = MCQAnswer.objects.create(
                    attempt=attempt,
                    question=q,
                    selected_option=None,
                    is_correct=False,
                    marks_obtained=0.0
                )
            else:
                answer.is_correct = False
                answer.marks_obtained = 0.0
                answer.save()

    total_questions = questions.count()
    wrong_count = answered_count - correct_count
    unanswered_count = total_questions - answered_count
    percentage = round((obtained_marks / total_marks) * 100, 2) if total_marks > 0 else 0.0

    # Update attempt
    attempt.status = AttemptStatus.COMPLETED
    attempt.submitted_at = timezone.now()
    attempt.total_score = obtained_marks
    attempt.max_score = total_marks
    attempt.save()

    # Create or update Result
    AssessmentResult.objects.update_or_create(
        attempt=attempt,
        defaults={
            'total_marks': total_marks,
            'obtained_marks': obtained_marks,
            'percentage': percentage,
        }
    )

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "total_marks": total_marks,
        "obtained_marks": obtained_marks,
        "percentage": percentage,
        "correct_answers": correct_count,
        "wrong_answers": wrong_count,
        "unanswered": unanswered_count
    }


class MCQAssessmentStartView(APIView):
    """
    POST /api/assessments/mcq/start/
    Initiates a new MCQ assessment session for a student or guest.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        category = request.data.get('category')
        difficulty = request.data.get('difficulty')
        question_count = request.data.get('question_count', 5)

        # Validation
        valid_categories = [Category.GENERAL_KNOWLEDGE, Category.ENGLISH, Category.MATHEMATICS]
        if category not in valid_categories:
            return Response(
                {"error": f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_difficulties = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
        if difficulty not in valid_difficulties:
            return Response(
                {"error": f"Invalid difficulty '{difficulty}'. Must be one of: {', '.join(valid_difficulties)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            question_count = int(question_count)
            if question_count <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"error": "question_count must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Server-side selection and safe randomization
        available_questions = list(Question.objects.filter(
            question_type=QuestionType.MCQ,
            category=category,
            difficulty=difficulty,
            is_active=True
        ).order_by('?')[:question_count])

        if not available_questions:
            return Response(
                {"error": f"No questions available for category '{category}' and difficulty '{difficulty}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate time limit and total score
        time_limit = sum(q.time_limit for q in available_questions)
        max_score = sum(q.marks for q in available_questions)

        # Determine user / session identity
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_id = uuid.uuid4().hex if user is None else ''

        # Create Attempt
        attempt = AssessmentAttempt.objects.create(
            user=user,
            session_id=session_id,
            question_type=QuestionType.MCQ,
            category=category,
            difficulty=difficulty,
            status=AttemptStatus.IN_PROGRESS,
            total_score=0.0,
            max_score=max_score,
            time_limit_seconds=time_limit
        )
        attempt.questions.set(available_questions)

        # Prepare sanitized question payload (STRICTLY NO is_correct)
        questions_payload = []
        for q in available_questions:
            options_data = QuestionOptionStudentSerializer(q.options.all().order_by('option_key'), many=True).data
            questions_payload.append({
                "id": q.id,
                "title": q.title,
                "description": q.description,
                "marks": q.marks,
                "time_limit": q.time_limit,
                "options": options_data
            })

        return Response({
            "attempt_id": attempt.id,
            "session_id": session_id if attempt.is_guest else None,
            "category": attempt.category,
            "difficulty": attempt.difficulty,
            "total_questions": len(available_questions),
            "max_score": attempt.max_score,
            "time_limit_seconds": attempt.time_limit_seconds,
            "started_at": attempt.started_at.isoformat(),
            "questions": questions_payload
        }, status=status.HTTP_201_CREATED)


class MCQAssessmentAnswerView(APIView):
    """
    POST /api/assessments/mcq/<int:attempt_id>/answer/
    Records or updates a chosen option for a question in an in-progress assessment.
    """
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        # Check attempt status
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": f"Cannot submit answers: Assessment is {attempt.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Server-side timer verification
        if attempt.is_time_expired:
            evaluate_attempt_server_side(attempt)
            return Response(
                {"error": "Assessment time limit has expired. Your attempt has been automatically submitted.", "expired": True},
                status=status.HTTP_400_BAD_REQUEST
            )

        question_id = request.data.get('question_id')
        option_id = request.data.get('option_id')

        if not question_id:
            return Response({"error": "question_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify question belongs to this attempt
        if not attempt.questions.filter(id=question_id).exists():
            return Response(
                {"error": "Question does not belong to this assessment attempt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = get_object_or_404(Question, id=question_id)

        # If option_id is provided, verify it belongs to this question
        option = None
        if option_id is not None:
            try:
                option = QuestionOption.objects.get(id=option_id, question=question)
            except QuestionOption.DoesNotExist:
                return Response(
                    {"error": "Invalid option for this question."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Save or update answer record (do not reveal correctness to client)
        answer, _ = MCQAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={'selected_option': option}
        )

        return Response({
            "status": "ok",
            "message": "Answer recorded.",
            "question_id": question.id,
            "option_id": option.id if option else None,
            "option_key": option.option_key if option else None
        }, status=status.HTTP_200_OK)


class MCQAssessmentSubmitView(APIView):
    """
    POST /api/assessments/mcq/<int:attempt_id>/submit/
    Submits the assessment, executes authoritative server-side scoring,
    and returns the official score and accuracy metrics.
    """
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        # Prevent double submission
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": "Assessment has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result_data = evaluate_attempt_server_side(attempt)
        return Response(result_data, status=status.HTTP_200_OK)


class MCQAssessmentResultView(APIView):
    """
    GET /api/assessments/mcq/<int:attempt_id>/result/
    Returns completed score metrics and question-by-question review with explanations.
    """
    permission_classes = [AllowAny]

    def get(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.status == AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": "Assessment is still in progress. Please submit before viewing results."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = getattr(attempt, 'result', None)
        answers = attempt.mcq_answers.select_related('question', 'selected_option').all()

        total_questions = attempt.questions.count()
        correct_count = answers.filter(is_correct=True).count()
        answered_count = answers.filter(selected_option__isnull=False).count()
        wrong_count = answered_count - correct_count
        unanswered_count = total_questions - answered_count

        time_taken = None
        if attempt.submitted_at and attempt.started_at:
            time_taken = max(0, int((attempt.submitted_at - attempt.started_at).total_seconds()))

        # Question-by-question review (revealed only upon completion)
        review = []
        for q in attempt.questions.all().order_by('id'):
            ans = answers.filter(question=q).first()
            correct_opt = q.options.filter(is_correct=True).first()

            review.append({
                "question_id": q.id,
                "title": q.title,
                "description": q.description,
                "marks": q.marks,
                "marks_obtained": ans.marks_obtained if ans else 0.0,
                "is_correct": ans.is_correct if ans else False,
                "selected_option_id": ans.selected_option.id if (ans and ans.selected_option) else None,
                "selected_option_key": ans.selected_option.option_key if (ans and ans.selected_option) else None,
                "selected_option_text": ans.selected_option.option_text if (ans and ans.selected_option) else None,
                "correct_option_id": correct_opt.id if correct_opt else None,
                "correct_option_key": correct_opt.option_key if correct_opt else None,
                "correct_option_text": correct_opt.option_text if correct_opt else None,
                "explanation": q.explanation or "No explanation provided for this question."
            })

        return Response({
            "attempt_id": attempt.id,
            "status": attempt.status,
            "category": attempt.category,
            "difficulty": attempt.difficulty,
            "total_marks": result.total_marks if result else attempt.max_score,
            "obtained_marks": result.obtained_marks if result else attempt.total_score,
            "percentage": result.percentage if result else 0.0,
            "correct_answers": correct_count,
            "wrong_answers": wrong_count,
            "unanswered": unanswered_count,
            "time_taken_seconds": time_taken,
            "started_at": attempt.started_at.isoformat(),
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            "review": review
        }, status=status.HTTP_200_OK)


class MyAssessmentAttemptsView(APIView):
    """
    GET /api/assessments/my-attempts/
    Lists assessment attempts for the currently authenticated student or guest session.
    Strictly isolated: students can never access other students' attempts, and guests
    only access attempts matching their session ID.
    Supports filtering by query parameters:
      - type / question_type: 'MCQ' or 'CODE'
      - category: filter by subject/category (case-insensitive)
      - status: 'COMPLETED', 'IN_PROGRESS', etc.
      - limit: max number of attempts to return
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user and request.user.is_authenticated:
            attempts = AssessmentAttempt.objects.filter(user=request.user)
        else:
            session_id = (
                request.query_params.get('session_id') or
                request.headers.get('X-Session-ID')
            )
            if not session_id:
                return Response(
                    {"error": "Authentication credentials or guest session_id required."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            attempts = AssessmentAttempt.objects.filter(user__isnull=True, session_id=session_id)

        # Filters
        q_type = request.query_params.get('type') or request.query_params.get('question_type')
        if q_type:
            q_type = q_type.upper().strip()
            if q_type in [QuestionType.MCQ, QuestionType.CODE]:
                attempts = attempts.filter(question_type=q_type)

        category = request.query_params.get('category')
        if category:
            attempts = attempts.filter(category__iexact=category.strip())

        attempt_status = request.query_params.get('status')
        if attempt_status:
            attempts = attempts.filter(status__iexact=attempt_status.strip())

        attempts = attempts.order_by('-started_at')

        limit = request.query_params.get('limit')
        if limit:
            try:
                limit_val = int(limit)
                if limit_val > 0:
                    attempts = attempts[:limit_val]
            except (ValueError, TypeError):
                pass

        data = []
        for att in attempts:
            res = getattr(att, 'result', None)
            pct = res.percentage if res else (
                round((att.total_score / att.max_score) * 100, 1) if att.max_score > 0 else 0.0
            )

            # Determine appropriate action URL
            if att.question_type == QuestionType.CODE:
                result_url = (
                    f"/coding/result/{att.id}/"
                    if att.status == AttemptStatus.COMPLETED
                    else f"/coding/assessment/{att.id}/"
                )
            else:
                result_url = (
                    f"/assessments/mcq/{att.id}/result/"
                    if att.status == AttemptStatus.COMPLETED
                    else f"/assessments/mcq/{att.id}/"
                )

            data.append({
                "attempt_id": att.id,
                "question_type": att.question_type,
                "category": att.category,
                "difficulty": att.difficulty,
                "language": att.language,
                "status": att.status,
                "total_score": att.total_score,
                "max_score": att.max_score,
                "percentage": round(float(pct), 1),
                "started_at": att.started_at.isoformat(),
                "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
                "result_url": result_url
            })
        return Response(data, status=status.HTTP_200_OK)


class AssessmentProgressView(APIView):
    """
    GET /api/assessments/progress/
    Computes overall assessment performance metrics, summary stats, and breakdown
    for the authenticated student or guest session.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user and request.user.is_authenticated:
            attempts = AssessmentAttempt.objects.filter(user=request.user)
        else:
            session_id = (
                request.query_params.get('session_id') or
                request.headers.get('X-Session-ID')
            )
            if not session_id:
                return Response(
                    {"error": "Authentication credentials or guest session_id required."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            attempts = AssessmentAttempt.objects.filter(user__isnull=True, session_id=session_id)

        total_attempts = attempts.count()
        completed_attempts = attempts.filter(status=AttemptStatus.COMPLETED)
        completed_count = completed_attempts.count()
        in_progress_count = attempts.filter(status=AttemptStatus.IN_PROGRESS).count()

        mcq_count = attempts.filter(question_type=QuestionType.MCQ).count()
        coding_count = attempts.filter(question_type=QuestionType.CODE).count()

        # Score & Percentage averages over completed attempts
        total_pct = 0.0
        total_score_sum = 0.0
        for att in completed_attempts:
            res = getattr(att, 'result', None)
            if res:
                total_pct += res.percentage
                total_score_sum += res.obtained_marks
            elif att.max_score > 0:
                pct = (att.total_score / att.max_score) * 100
                total_pct += pct
                total_score_sum += att.total_score

        avg_pct = round(total_pct / completed_count, 1) if completed_count > 0 else 0.0
        avg_score = round(total_score_sum / completed_count, 1) if completed_count > 0 else 0.0

        # Category Breakdown
        categories_map = {}
        for att in attempts:
            cat = att.category
            if cat not in categories_map:
                categories_map[cat] = {
                    "category": cat,
                    "question_type": att.question_type,
                    "total": 0,
                    "completed": 0,
                    "total_percentage": 0.0,
                    "average_percentage": 0.0
                }
            categories_map[cat]["total"] += 1
            if att.status == AttemptStatus.COMPLETED:
                categories_map[cat]["completed"] += 1
                res = getattr(att, 'result', None)
                if res:
                    categories_map[cat]["total_percentage"] += res.percentage
                elif att.max_score > 0:
                    categories_map[cat]["total_percentage"] += (att.total_score / att.max_score) * 100

        for cat_info in categories_map.values():
            if cat_info["completed"] > 0:
                cat_info["average_percentage"] = round(cat_info["total_percentage"] / cat_info["completed"], 1)
            else:
                cat_info["average_percentage"] = 0.0
            del cat_info["total_percentage"]

        # Recent 5 attempts
        recent_qs = attempts.order_by('-started_at')[:5]
        recent_data = []
        for att in recent_qs:
            res = getattr(att, 'result', None)
            pct = res.percentage if res else (
                round((att.total_score / att.max_score) * 100, 1) if att.max_score > 0 else 0.0
            )
            if att.question_type == QuestionType.CODE:
                result_url = (
                    f"/coding/result/{att.id}/"
                    if att.status == AttemptStatus.COMPLETED
                    else f"/coding/assessment/{att.id}/"
                )
            else:
                result_url = (
                    f"/assessments/mcq/{att.id}/result/"
                    if att.status == AttemptStatus.COMPLETED
                    else f"/assessments/mcq/{att.id}/"
                )

            recent_data.append({
                "attempt_id": att.id,
                "question_type": att.question_type,
                "category": att.category,
                "difficulty": att.difficulty,
                "language": att.language,
                "status": att.status,
                "total_score": att.total_score,
                "max_score": att.max_score,
                "percentage": round(float(pct), 1),
                "started_at": att.started_at.isoformat(),
                "submitted_at": att.submitted_at.isoformat() if att.submitted_at else None,
                "result_url": result_url
            })

        user_param = request.user if (request.user and request.user.is_authenticated) else None
        session_param = None if user_param else session_id
        unified_data = compute_student_progress_and_mastery(user=user_param, session_id=session_param)

        return Response({
            "total_attempts": total_attempts,
            "completed_attempts": completed_count,
            "in_progress_attempts": in_progress_count,
            "mcq_count": mcq_count,
            "coding_count": coding_count,
            "average_percentage": avg_pct,
            "average_score": avg_score,
            "unified_score": unified_data["unified_score"],
            "theory_score": unified_data["theory_score"],
            "coding_score": unified_data["coding_score"],
            "unique_questions_count": unified_data["unique_questions_count"],
            "skill_tier": unified_data["skill_tier"],
            "skill_badge_class": unified_data["skill_badge_class"],
            "category_mastery": unified_data["category_mastery"],
            "category_breakdown": list(categories_map.values()),
            "recent_attempts": recent_data
        }, status=status.HTTP_200_OK)


class CodingAssessmentStartView(APIView):
    """
    POST /api/assessments/coding/start/
    Initiates a new Live Coding Assessment session for a student or guest.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        question_id = request.data.get('question_id')
        category = request.data.get('category')
        difficulty = request.data.get('difficulty')
        language = request.data.get('language')
        time_limit_seconds = request.data.get('time_limit_seconds', 1800)

        # 1. Fetch Question
        if question_id:
            try:
                question = Question.objects.get(
                    id=question_id,
                    question_type=QuestionType.CODE,
                    is_active=True
                )
            except Question.DoesNotExist:
                return Response(
                    {"error": f"Active coding question with ID '{question_id}' not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            qs = Question.objects.filter(question_type=QuestionType.CODE, is_active=True)
            if category:
                qs = qs.filter(category__iexact=category)
            if difficulty:
                qs = qs.filter(difficulty__iexact=difficulty)

            question = qs.order_by('?').first()
            if not question:
                filter_desc = []
                if category:
                    filter_desc.append(f"category '{category}'")
                if difficulty:
                    filter_desc.append(f"difficulty '{difficulty}'")
                desc = " and ".join(filter_desc) or "the specified criteria"
                return Response(
                    {"error": f"No active coding questions available matching {desc}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 2. Validate Language
        valid_languages = ['python', 'java', 'cpp']
        if not language:
            # Infer language from question category if applicable
            cat_lower = question.category.lower()
            if 'java' in cat_lower:
                language = 'java'
            elif 'c++' in cat_lower or 'cpp' in cat_lower:
                language = 'cpp'
            else:
                language = 'python'
        else:
            language = str(language).strip().lower()

        if language not in valid_languages:
            return Response(
                {"error": f"Invalid language '{language}'. Supported languages are: {', '.join(valid_languages)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Validate Time Limit
        try:
            time_limit_seconds = int(time_limit_seconds)
            if time_limit_seconds <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            time_limit_seconds = 1800

        # 4. User / Guest Session
        user = request.user if (request.user and request.user.is_authenticated) else None
        session_id = '' if user else (request.data.get('session_id') or uuid.uuid4().hex)

        # 5. Create AssessmentAttempt
        attempt = AssessmentAttempt.objects.create(
            user=user,
            session_id=session_id,
            question_type=QuestionType.CODE,
            category=question.category,
            difficulty=question.difficulty,
            language=language,
            status=AttemptStatus.IN_PROGRESS,
            total_score=0.0,
            max_score=question.marks,
            time_limit_seconds=time_limit_seconds
        )
        attempt.questions.set([question])

        # 6. Build Sanitized Question Payload (NEVER expose hidden test cases)
        sample_cases = TestCaseStudentSerializer(
            question.test_cases.filter(is_hidden=False),
            many=True
        ).data

        question_payload = {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "category": question.category,
            "difficulty": question.difficulty,
            "marks": question.marks,
            "time_limit": question.time_limit,
            "memory_limit": question.memory_limit,
            "input_format": question.input_format,
            "output_format": question.output_format,
            "constraints": question.constraints,
            "sample_input": question.sample_input,
            "sample_output": question.sample_output,
            "starter_code": question.starter_code or {},
            "sample_test_cases": sample_cases,
        }

        return Response({
            "attempt_id": attempt.id,
            "session_id": session_id if attempt.is_guest else None,
            "category": attempt.category,
            "difficulty": attempt.difficulty,
            "language": attempt.language,
            "time_limit_seconds": attempt.time_limit_seconds,
            "started_at": attempt.started_at.isoformat(),
            "question": question_payload
        }, status=status.HTTP_201_CREATED)


class CodingAssessmentDetailView(APIView):
    """
    GET /api/assessments/coding/<int:attempt_id>/
    Retrieves live coding workspace state, time remaining, and problem statement.
    """
    permission_classes = [AllowAny]

    def get(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.question_type != QuestionType.CODE:
            return Response(
                {"error": "This attempt is not a Coding assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remaining seconds calculation
        remaining_seconds = 0
        if attempt.time_limit_seconds and attempt.started_at:
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            remaining_seconds = max(0, int(attempt.time_limit_seconds - elapsed))

        question = attempt.questions.first()
        question_payload = None
        if question:
            sample_cases = TestCaseStudentSerializer(
                question.test_cases.filter(is_hidden=False),
                many=True
            ).data
            question_payload = {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "category": question.category,
                "difficulty": question.difficulty,
                "marks": question.marks,
                "time_limit": question.time_limit,
                "memory_limit": question.memory_limit,
                "input_format": question.input_format,
                "output_format": question.output_format,
                "constraints": question.constraints,
                "sample_input": question.sample_input,
                "sample_output": question.sample_output,
                "starter_code": question.starter_code or {},
                "sample_test_cases": sample_cases,
            }

        latest_submission = attempt.coding_submissions.order_by('-created_at').first()

        return Response({
            "attempt_id": attempt.id,
            "status": attempt.status,
            "category": attempt.category,
            "difficulty": attempt.difficulty,
            "language": attempt.language,
            "started_at": attempt.started_at.isoformat(),
            "time_limit_seconds": attempt.time_limit_seconds,
            "remaining_seconds": remaining_seconds,
            "is_time_expired": attempt.is_time_expired,
            "question": question_payload,
            "saved_code": latest_submission.source_code if latest_submission else None,
            "submission_status": latest_submission.status if latest_submission else None,
        }, status=status.HTTP_200_OK)


class CodingAssessmentRunCodeView(APIView):
    """
    POST /api/assessments/coding/<int:attempt_id>/run/
    Executes candidate code against PUBLIC/SAMPLE test cases ONLY.
    Does NOT finalize the attempt, does NOT touch AssessmentResult,
    and NEVER queries, evaluates, or leaks hidden test cases.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'code_run'

    def post(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.question_type != QuestionType.CODE:
            return Response(
                {"error": "This attempt is not a Coding assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": f"Cannot run code: Assessment is already {attempt.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attempt.is_time_expired:
            return Response(
                {"error": "Assessment time limit has expired.", "expired": True},
                status=status.HTTP_400_BAD_REQUEST
            )

        source_code = request.data.get('source_code', '')
        if not source_code or not source_code.strip():
            return Response(
                {"error": "Source code cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        language = request.data.get('language') or attempt.language or 'python'
        language_id = LANGUAGE_IDS.get(language.lower(), 71)

        question = attempt.questions.first()
        if not question:
            return Response(
                {"error": "Associated question not found for this attempt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # STRICT SECURITY: Query ONLY sample/public test cases (is_hidden=False)
        sample_cases = question.test_cases.filter(is_hidden=False)
        sample_results = []
        passed_count = 0
        total_time = 0.0
        max_memory = 0.0
        overall_status = SubmissionStatus.ACCEPTED
        overall_error = ""

        try:
            for idx, tc in enumerate(sample_cases):
                result = Judge0Service.execute_test_case(
                    source_code=source_code,
                    language_id=language_id,
                    test_case=tc,
                )

                status_id = result.get("status_id", 0)
                t = float(result.get("time") or 0.0)
                m = float(result.get("memory") or 0.0)
                total_time += t
                if m > max_memory:
                    max_memory = m

                is_passed = (status_id == 3)
                if is_passed:
                    passed_count += 1
                else:
                    if status_id == 6:
                        overall_status = SubmissionStatus.COMPILATION_ERROR
                        overall_error = result.get("compile_output") or result.get("stderr") or ""
                    elif status_id in (7, 8, 9, 10, 11, 12):
                        overall_status = SubmissionStatus.RUNTIME_ERROR
                        overall_error = result.get("stderr") or ""
                    elif status_id == 5:
                        overall_status = SubmissionStatus.TIME_LIMIT_EXCEEDED
                        overall_error = result.get("message") or ""
                    elif status_id == 13:
                        overall_status = SubmissionStatus.SERVICE_UNAVAILABLE
                        overall_error = result.get("message") or ""
                    else:
                        if overall_status == SubmissionStatus.ACCEPTED:
                            overall_status = SubmissionStatus.WRONG_ANSWER
                        overall_error = result.get("stderr") or result.get("message") or ""

                sample_results.append({
                    "case_number": idx + 1,
                    "test_case_number": idx + 1,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "actual_output": result.get("stdout") or "",
                    "passed": is_passed,
                    "status_id": status_id,
                    "status_description": result.get("status_description") or ("Accepted" if is_passed else "Failed"),
                    "execution_time": t,
                    "memory": m,
                    "stderr": result.get("stderr") or "",
                    "compile_output": result.get("compile_output") or "",
                })

            if len(sample_cases) > 0:
                if passed_count == len(sample_cases):
                    overall_status = SubmissionStatus.ACCEPTED
                elif passed_count > 0:
                    overall_status = SubmissionStatus.PARTIAL
            else:
                overall_status = "NO_TEST_CASES"

        except (TimeoutError, requests.RequestException) as exc:
            overall_status = SubmissionStatus.SERVICE_UNAVAILABLE
            overall_error = str(exc)

        return Response({
            "status": overall_status,
            "language": language,
            "sample_cases_passed": passed_count,
            "total_sample_cases": len(sample_cases),
            "execution_time": round(total_time, 3),
            "memory_usage": max_memory,
            "error_output": overall_error,
            "results": sample_results,
            "test_cases": sample_results,
            "message": "Run Code completed against sample test cases."
        }, status=status.HTTP_200_OK)


class CodingAssessmentSubmitView(APIView):
    """
    POST /api/assessments/coding/<int:attempt_id>/submit/
    Submits user's code solution for an active coding assessment.
    Stores submission in database with PENDING status (ready for Judge0 in Phase 6).
    """
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.question_type != QuestionType.CODE:
            return Response(
                {"error": "This attempt is not a Coding assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent double submission
        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": f"Cannot submit: Assessment is already {attempt.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check time expiry
        if attempt.is_time_expired:
            attempt.status = AttemptStatus.COMPLETED
            attempt.submitted_at = timezone.now()
            attempt.save()
            return Response(
                {"error": "Assessment time limit has expired. Your attempt has ended.", "expired": True},
                status=status.HTTP_400_BAD_REQUEST
            )

        source_code = request.data.get('source_code', '')
        if not source_code or not source_code.strip():
            return Response(
                {"error": "Source code cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        language = request.data.get('language') or attempt.language or 'python'
        language = str(language).strip().lower()
        valid_languages = ['python', 'java', 'cpp']
        if language not in valid_languages:
            return Response(
                {"error": f"Unsupported language '{language}'. Supported languages: {', '.join(valid_languages)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = attempt.questions.first()
        if not question:
            return Response(
                {"error": "No question associated with this attempt."},
                status=status.HTTP_400_BAD_REQUEST
            )

               # Get Judge0 language ID
        language_id = LANGUAGE_IDS.get(language)

        if not language_id:
            return Response(
                {"error": f"Unsupported coding language: {language}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all test cases, including hidden cases
        test_cases = list(
            question.test_cases.all().order_by('is_hidden', 'id')
        )

        if not test_cases:
            return Response(
                {"error": "No test cases are configured for this question."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create submission record before execution
        submission = CodingSubmission.objects.create(
            attempt=attempt,
            user=attempt.user,
            question=question,
            language=language,
            source_code=source_code,
            status=SubmissionStatus.PENDING,
            score=0.0,
            passed_test_cases=0,
            total_test_cases=len(test_cases),
        )

        passed_count = 0
        total_execution_time = 0.0
        max_memory_usage = 0
        final_status = SubmissionStatus.WRONG_ANSWER
        error_output = ""

        try:
            for test_case in test_cases:
                result = Judge0Service.execute_test_case(
                    source_code=source_code,
                    language_id=language_id,
                    test_case=test_case,
                )

                status_id = result["status_id"]

                if result["time"]:
                    total_execution_time += float(result["time"])

                if result["memory"]:
                    max_memory_usage = max(
                        max_memory_usage,
                        int(result["memory"])
                    )

                # Judge0 status 3 = Accepted
                if status_id == 3:
                    passed_count += 1
                    continue

                # Compilation Error
                if status_id == 6:
                    final_status = SubmissionStatus.COMPILATION_ERROR
                    error_output = result["compile_output"] or ""
                    break

                # Runtime Error
                if status_id == 7:
                    final_status = SubmissionStatus.RUNTIME_ERROR
                    error_output = result["stderr"] or ""
                    break

                # Time Limit Exceeded
                if status_id == 5:
                    final_status = SubmissionStatus.TIME_LIMIT_EXCEEDED
                    error_output = result["message"] or ""
                    break

                # Judge0 internal/service error
                if status_id == 13:
                    final_status = SubmissionStatus.SERVICE_UNAVAILABLE
                    error_output = result["message"] or ""
                    break

                # Any other failed execution
                final_status = SubmissionStatus.WRONG_ANSWER
                error_output = (
                    result["stderr"]
                    or result["message"]
                    or ""
                )
                break

            # Calculate partial score
            score = 0.0

            if passed_count == len(test_cases):
                final_status = SubmissionStatus.ACCEPTED
                score = float(question.marks)

            elif passed_count > 0:
                final_status = SubmissionStatus.PARTIAL
                score = round(
                    question.marks * passed_count / len(test_cases),
                    2
                )

            else:
                if final_status == SubmissionStatus.WRONG_ANSWER:
                    score = 0.0

        except (TimeoutError, requests.RequestException) as exc:
            final_status = SubmissionStatus.SERVICE_UNAVAILABLE
            error_output = str(exc)
            score = 0.0

        # Update submission with Judge0 results
        submission.judge0_token = result.get("token", "") if "result" in locals() else ""
        submission.status = final_status
        submission.score = score
        submission.passed_test_cases = passed_count
        submission.total_test_cases = len(test_cases)
        submission.execution_time = total_execution_time
        submission.memory_usage = max_memory_usage
        submission.error_output = error_output
        submission.save()

        # Complete the attempt
        attempt.status = AttemptStatus.COMPLETED
        attempt.submitted_at = timezone.now()
        attempt.language = language
        attempt.total_score = score
        attempt.save()

        # Update or create AssessmentResult
        percentage = (
            (score / question.marks) * 100
            if question.marks
            else 0.0
        )

        AssessmentResult.objects.update_or_create(
            attempt=attempt,
            defaults={
                "total_marks": question.marks,
                "obtained_marks": score,
                "percentage": percentage,
            }
        )

        return Response({
            "submission_id": submission.id,
            "attempt_id": attempt.id,
            "status": submission.status,
            "language": submission.language,
            "score": submission.score,
            "passed_test_cases": submission.passed_test_cases,
            "total_test_cases": submission.total_test_cases,
            "execution_time": submission.execution_time,
            "memory_usage": submission.memory_usage,
            "error_output": submission.error_output,
            "message": "Code evaluated successfully.",
            "submitted_at": submission.created_at.isoformat()
        }, status=status.HTTP_200_OK)


class CodingAssessmentResultView(APIView):
    """
    GET /api/assessments/coding/<int:attempt_id>/result/
    Retrieves the final results, submission details, and problem details
    for a completed coding assessment.
    """
    permission_classes = [AllowAny]

    def get(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.question_type != QuestionType.CODE:
            return Response(
                {"error": "This attempt is not a Coding assessment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attempt.status == AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": "Assessment is still in progress. Submit your solution to view results."},
                status=status.HTTP_400_BAD_REQUEST
            )

        latest_submission = attempt.coding_submissions.order_by('-created_at').first()
        question = attempt.questions.first()

        time_taken_seconds = 0
        if attempt.submitted_at and attempt.started_at:
            time_taken_seconds = max(0, int((attempt.submitted_at - attempt.started_at).total_seconds()))

        question_payload = None
        if question:
            sample_cases = TestCaseStudentSerializer(
                question.test_cases.filter(is_hidden=False),
                many=True
            ).data
            question_payload = {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "category": question.category,
                "difficulty": question.difficulty,
                "constraints": question.constraints,
                "input_format": question.input_format,
                "output_format": question.output_format,
                "sample_input": question.sample_input,
                "sample_output": question.sample_output,
                "sample_test_cases": sample_cases,
            }

        res_obj = getattr(attempt, 'result', None)
        total_marks = res_obj.total_marks if res_obj else (question.marks if question else attempt.max_score)
        obtained_marks = res_obj.obtained_marks if res_obj else (latest_submission.score if latest_submission else attempt.total_score)
        percentage = res_obj.percentage if res_obj else ((obtained_marks / total_marks * 100) if total_marks else 0.0)

        return Response({
            "attempt_id": attempt.id,
            "status": attempt.status,
            "question_type": attempt.question_type,
            "category": attempt.category,
            "difficulty": attempt.difficulty,
            "language": latest_submission.language if latest_submission else attempt.language,
            "submission_id": latest_submission.id if latest_submission else None,
            "submission_status": latest_submission.status if latest_submission else None,
            "source_code": latest_submission.source_code if latest_submission else "",
            "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else (latest_submission.created_at.isoformat() if latest_submission else None),
            "time_taken_seconds": time_taken_seconds,
            "total_marks": total_marks,
            "obtained_marks": obtained_marks,
            "percentage": round(percentage, 2),
            "passed_test_cases": latest_submission.passed_test_cases if latest_submission else 0,
            "total_test_cases": latest_submission.total_test_cases if latest_submission else 0,
            "execution_time": latest_submission.execution_time if latest_submission else 0.0,
            "memory_usage": latest_submission.memory_usage if latest_submission else 0,
            "error_output": latest_submission.error_output if latest_submission else "",
            "execution_notice": "Automated grading scheduled via Judge0 API in Phase 6.",
            "question": question_payload,
        }, status=status.HTTP_200_OK)


class AssessmentAbandonView(APIView):
    """
    POST /api/assessments/<int:attempt_id>/abandon/
    Gracefully abandons an in-progress assessment attempt (Phase 11).
    """
    permission_classes = [AllowAny]

    def post(self, request, attempt_id):
        attempt, error_response = get_attempt_for_request(attempt_id, request)
        if error_response:
            return error_response

        if attempt.status != AttemptStatus.IN_PROGRESS:
            return Response(
                {"error": f"Cannot abandon assessment: Attempt is already {attempt.get_status_display().lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        attempt.status = AttemptStatus.ABANDONED
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=['status', 'submitted_at'])

        return Response({
            "status": "success",
            "message": "Assessment attempt has been abandoned.",
            "attempt_id": attempt.id,
            "attempt_status": attempt.status,
        }, status=status.HTTP_200_OK)


class ActiveAssessmentAttemptView(APIView):
    """
    GET /api/assessments/active/
    Returns the most recent active in-progress assessment attempt for the current user or guest (Phase 11).
    Also performs server-side auto-expiry for expired attempts.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None

        if user:
            in_progress_attempts = AssessmentAttempt.objects.filter(
                user=user,
                status=AttemptStatus.IN_PROGRESS
            ).order_by('-started_at')
        else:
            session_id = (
                request.query_params.get('session_id') or
                request.headers.get('X-Session-ID') or
                request.COOKIES.get('sessionid')
            )
            if not session_id:
                return Response({"has_active_attempt": False, "attempt": None}, status=status.HTTP_200_OK)
            in_progress_attempts = AssessmentAttempt.objects.filter(
                session_id=session_id,
                user__isnull=True,
                status=AttemptStatus.IN_PROGRESS
            ).order_by('-started_at')

        for attempt in in_progress_attempts:
            if attempt.is_time_expired:
                # Expired attempt: auto-expire by setting submitted_at
                if not attempt.submitted_at:
                    attempt.submitted_at = timezone.now()
                    attempt.save(update_fields=['submitted_at'])
                continue

            # Active unexpired attempt found
            remaining_seconds = 0
            if attempt.started_at and attempt.time_limit_seconds:
                elapsed = (timezone.now() - attempt.started_at).total_seconds()
                remaining_seconds = max(0, int(attempt.time_limit_seconds - elapsed))

            resume_url = (
                f"/assessments/mcq/{attempt.id}/"
                if attempt.question_type == QuestionType.MCQ
                else f"/coding/assessment/{attempt.id}/"
            )

            return Response({
                "has_active_attempt": True,
                "attempt": {
                    "id": attempt.id,
                    "question_type": attempt.question_type,
                    "category": attempt.category,
                    "difficulty": attempt.difficulty,
                    "remaining_seconds": remaining_seconds,
                    "resume_url": resume_url,
                }
            }, status=status.HTTP_200_OK)

        return Response({"has_active_attempt": False, "attempt": None}, status=status.HTTP_200_OK)

