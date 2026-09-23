"""
Leaderboard Views for SKILLBYTE (Phase 10).
Provides overall and category-wise rankings based on the approved
Best Score per Unique Question deduplication policy and timeframe scoping.
"""

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from accounts.models import Role
from .models import (
    AssessmentAttempt,
    AttemptStatus,
    QuestionType,
    Category,
)
from .scoring_service import get_skill_tier


class LeaderboardView(APIView):
    """
    GET /api/leaderboard/
    Public read-only leaderboard displaying overall and category-wise student rankings.
    Query parameters:
    - category: string (e.g. 'all', 'Python', 'Mathematics', 'General Knowledge', etc.)
    - timeframe: 'all_time' | 'month' | 'week' (default 'all_time')
    - limit: int (default 50)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get('category', 'all').strip()
        timeframe = request.query_params.get('timeframe', 'all_time').strip().lower()
        try:
            limit = min(max(1, int(request.query_params.get('limit', 50))), 100)
        except ValueError:
            limit = 50

        # Base query: completed attempts by registered STUDENT users
        attempts_qs = AssessmentAttempt.objects.filter(
            status=AttemptStatus.COMPLETED,
            user__isnull=False,
            user__profile__role=Role.STUDENT,
            user__is_staff=False,
            user__is_superuser=False
        )

        now = timezone.now()
        if timeframe == 'month':
            attempts_qs = attempts_qs.filter(submitted_at__gte=now - timedelta(days=30))
        elif timeframe == 'week':
            attempts_qs = attempts_qs.filter(submitted_at__gte=now - timedelta(days=7))

        if category and category.lower() != 'all':
            attempts_qs = attempts_qs.filter(category__iexact=category)

        # Optimize: prefetch questions, mcq_answers and user profile
        attempts = list(
            attempts_qs.select_related('user', 'user__profile')
            .prefetch_related('questions', 'mcq_answers__question')
        )

        # Structure: user_id -> { user: User, best_per_q: { q_id: { best_marks, max_marks, type } } }
        students_map = {}

        for att in attempts:
            uid = att.user_id
            if uid not in students_map:
                students_map[uid] = {
                    'user': att.user,
                    'best_per_q': {}
                }

            user_best = students_map[uid]['best_per_q']

            if att.question_type == QuestionType.CODE:
                q = att.questions.first()
                if q:
                    res = getattr(att, 'result', None)
                    obtained = float(res.obtained_marks) if res else float(att.total_score)
                    max_m = int(q.marks) if q.marks else int(att.max_score or 10)
                    if q.id not in user_best or obtained > user_best[q.id]['best_marks']:
                        user_best[q.id] = {
                            'best_marks': obtained,
                            'max_marks': max_m,
                            'type': QuestionType.CODE
                        }
            else:
                mcq_answers = list(att.mcq_answers.all())
                if mcq_answers:
                    for ans in mcq_answers:
                        q = ans.question
                        if not q:
                            continue
                        obtained = float(ans.marks_obtained)
                        max_m = int(q.marks) if q.marks else 1
                        if q.id not in user_best or obtained > user_best[q.id]['best_marks']:
                            user_best[q.id] = {
                                'best_marks': obtained,
                                'max_marks': max_m,
                                'type': QuestionType.MCQ
                            }
                else:
                    res = getattr(att, 'result', None)
                    obtained = float(res.obtained_marks) if res else float(att.total_score)
                    for q in att.questions.all():
                        max_m = int(q.marks) if q.marks else int(att.max_score or 1)
                        if q.id not in user_best or obtained > user_best[q.id]['best_marks']:
                            user_best[q.id] = {
                                'best_marks': obtained,
                                'max_marks': max_m,
                                'type': QuestionType.MCQ
                            }

        # Calculate student summary points and accuracy
        ranked_list = []
        for uid, data in students_map.items():
            user = data['user']
            best_dict = data['best_per_q']
            if not best_dict:
                continue

            total_pts = sum(item['best_marks'] for item in best_dict.values())
            sum_max = sum(item['max_marks'] for item in best_dict.values())
            theory_pts = sum(item['best_marks'] for item in best_dict.values() if item['type'] == QuestionType.MCQ)
            coding_pts = sum(item['best_marks'] for item in best_dict.values() if item['type'] == QuestionType.CODE)

            accuracy = round((total_pts / sum_max * 100), 1) if sum_max > 0 else 0.0
            skill_tier, skill_badge = get_skill_tier(total_pts)

            full_name = f"{user.first_name} {user.last_name}".strip() or user.username

            ranked_list.append({
                "user_id": user.id,
                "username": user.username,
                "name": full_name,
                "user_name": full_name,
                "total_score": round(total_pts, 1),
                "unified_score": round(total_pts, 1),
                "theory_score": round(theory_pts, 1),
                "coding_score": round(coding_pts, 1),
                "unique_questions_completed": len(best_dict),
                "total_attempts": len(best_dict),
                "accuracy_percentage": accuracy,
                "skill_tier": skill_tier,
                "skill_badge_class": skill_badge,
            })

        # Sort: 1. -total_score, 2. -accuracy_percentage, 3. -unique_questions_completed, 4. username
        ranked_list.sort(key=lambda s: (-s['total_score'], -s['accuracy_percentage'], -s['unique_questions_completed'], s['username'].lower()))

        # Assign sequential rank positions
        for i, item in enumerate(ranked_list):
            item['rank'] = i + 1

        # Current user's rank (if authenticated student)
        current_user_rank = None
        if request.user and request.user.is_authenticated:
            # Check if user is a student
            if hasattr(request.user, 'profile') and request.user.profile.role == Role.STUDENT and not (request.user.is_staff or request.user.is_superuser):
                for item in ranked_list:
                    if item['user_id'] == request.user.id:
                        current_user_rank = {
                            "rank": item['rank'],
                            "user_id": item['user_id'],
                            "username": item['username'],
                            "name": item['name'],
                            "user_name": item['name'],
                            "total_score": item['total_score'],
                            "unified_score": item['unified_score'],
                            "theory_score": item['theory_score'],
                            "coding_score": item['coding_score'],
                            "accuracy_percentage": item['accuracy_percentage'],
                            "unique_questions_completed": item['unique_questions_completed'],
                            "total_attempts": item['total_attempts'],
                            "skill_tier": item['skill_tier'],
                            "skill_badge_class": item['skill_badge_class'],
                        }
                        break

        category_title = "All Categories" if (not category or category.lower() == 'all') else category

        return Response({
            "category": category_title,
            "timeframe": timeframe,
            "total_ranked_students": len(ranked_list),
            "current_user_rank": current_user_rank,
            "rankings": ranked_list[:limit],
            "leaderboard": ranked_list[:limit],
        }, status=status.HTTP_200_OK)

