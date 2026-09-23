"""
Admin Platform & Assessment Analytics Views for SKILLBYTE (Phase 10).
Accessible strictly to users with the ADMIN role.
"""

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import UserProfile, Role
from accounts.permissions import IsAdmin
from .models import (
    Question,
    QuestionType,
    Category,
    AssessmentAttempt,
    AttemptStatus,
    AssessmentResult,
    CodingSubmission,
    SubmissionStatus,
)


class AdminAnalyticsView(APIView):
    """
    GET /api/admin/analytics/
    Admin-only platform analytics, student engagement metrics,
    category-wise performance, and submission diagnostics.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # 1. Student Statistics
        total_students = UserProfile.objects.filter(role=Role.STUDENT).count()
        active_students_30d = (
            AssessmentAttempt.objects.filter(started_at__gte=thirty_days_ago, user__isnull=False)
            .values('user')
            .distinct()
            .count()
        )
        new_students_30d = User.objects.filter(
            date_joined__gte=thirty_days_ago, profile__role=Role.STUDENT
        ).count()

        # 2. Assessment Volume & Conversion
        total_attempts = AssessmentAttempt.objects.count()
        completed_attempts = AssessmentAttempt.objects.filter(status=AttemptStatus.COMPLETED).count()
        completion_rate = round((completed_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0.0
        mcq_attempts = AssessmentAttempt.objects.filter(question_type=QuestionType.MCQ).count()
        coding_attempts = AssessmentAttempt.objects.filter(question_type=QuestionType.CODE).count()

        # 3. Category Performance Diagnostics
        category_performance = []
        for cat_choice in Category.choices:
            cat_val = cat_choice[0]
            cat_attempts = AssessmentAttempt.objects.filter(category=cat_val, status=AttemptStatus.COMPLETED)
            count = cat_attempts.count()
            if count > 0:
                avg_pct = cat_attempts.aggregate(Avg('result__percentage'))['result__percentage__avg'] or 0.0
                passed_count = cat_attempts.filter(result__percentage__gte=60.0).count()
                pass_rate = round((passed_count / count * 100), 1)
            else:
                avg_pct = 0.0
                pass_rate = 0.0

            category_performance.append({
                "category": cat_val,
                "completed_attempts": count,
                "avg_percentage": round(avg_pct, 1),
                "pass_rate": pass_rate,
            })

        # 4. Coding Verdict Distribution
        verdict_counts = {}
        for status_choice in SubmissionStatus.choices:
            s_val = status_choice[0]
            verdict_counts[s_val] = CodingSubmission.objects.filter(status=s_val).count()

        # 5. Diagnostic: Hardest Questions (Lowest average score)
        completed_attempts_with_results = AssessmentAttempt.objects.filter(status=AttemptStatus.COMPLETED, questions__isnull=False)
        question_stats = {}
        for att in completed_attempts_with_results.prefetch_related('questions', 'result'):
            q = att.questions.first()
            if not q:
                continue
            res = getattr(att, 'result', None)
            pct = res.percentage if res else 0.0
            if q.id not in question_stats:
                question_stats[q.id] = {
                    "id": q.id,
                    "title": q.title,
                    "type": q.question_type,
                    "category": q.category,
                    "difficulty": q.difficulty,
                    "attempts": 0,
                    "total_pct": 0.0
                }
            question_stats[q.id]["attempts"] += 1
            question_stats[q.id]["total_pct"] += pct

        hardest_questions = []
        for q_id, q_data in question_stats.items():
            if q_data["attempts"] >= 1:
                avg_p = round(q_data["total_pct"] / q_data["attempts"], 1)
                fail_p = round(100.0 - avg_p, 1)
                hardest_questions.append({
                    "id": q_data["id"],
                    "question_id": q_data["id"],
                    "title": q_data["title"],
                    "type": q_data["type"],
                    "question_type": q_data["type"],
                    "category": q_data["category"],
                    "difficulty": q_data["difficulty"],
                    "attempts": q_data["attempts"],
                    "total_attempts": q_data["attempts"],
                    "attempts_count": q_data["attempts"],
                    "avg_percentage": avg_p,
                    "average_score_percent": avg_p,
                    "failure_rate_percent": fail_p,
                })

        hardest_questions.sort(key=lambda x: (x["avg_percentage"], -x["attempts_count"]))

        # Scoring metrics
        avg_score_pct = AssessmentResult.objects.aggregate(Avg('percentage'))['percentage__avg'] or 0.0
        mcq_avg_pct = AssessmentResult.objects.filter(attempt__question_type=QuestionType.MCQ).aggregate(Avg('percentage'))['percentage__avg'] or 0.0
        coding_avg_pct = AssessmentResult.objects.filter(attempt__question_type=QuestionType.CODE).aggregate(Avg('percentage'))['percentage__avg'] or 0.0

        mcq_completed = AssessmentAttempt.objects.filter(question_type=QuestionType.MCQ, status=AttemptStatus.COMPLETED).count()
        coding_completed = AssessmentAttempt.objects.filter(question_type=QuestionType.CODE, status=AttemptStatus.COMPLETED).count()

        # Format categories with aliases
        categories_formatted = []
        for cp in category_performance:
            categories_formatted.append({
                **cp,
                "total_attempts": AssessmentAttempt.objects.filter(category=cp["category"]).count(),
                "pass_rate_percent": cp["pass_rate"],
                "average_score_percent": cp["avg_percentage"],
            })

        return Response({
            "users": {
                "total_students": total_students,
                "active_30d": active_students_30d,
                "new_30d": new_students_30d,
            },
            "students": {
                "total_registered": total_students,
                "active_30d": active_students_30d,
                "new_30d": new_students_30d,
            },
            "attempts": {
                "total_initiated": total_attempts,
                "total_attempts": total_attempts,
                "completed_attempts": completed_attempts,
                "completion_rate_percent": completion_rate,
                "mcq_completed": mcq_completed,
                "coding_completed": coding_completed,
            },
            "assessments": {
                "total_attempts": total_attempts,
                "completed_attempts": completed_attempts,
                "completion_rate": completion_rate,
                "mcq_attempts": mcq_attempts,
                "coding_attempts": coding_attempts,
            },
            "scoring": {
                "platform_average_percent": round(avg_score_pct, 1),
                "mcq_average_percent": round(mcq_avg_pct, 1),
                "coding_average_percent": round(coding_avg_pct, 1),
            },
            "categories": categories_formatted,
            "category_performance": category_performance,
            "coding_verdicts": {
                **verdict_counts,
                "total_submissions": CodingSubmission.objects.count()
            },
            "hardest_questions": hardest_questions[:5],
        }, status=status.HTTP_200_OK)

