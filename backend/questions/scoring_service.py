"""
Scoring and Unified Progress Calculation Service for SKILLBYTE (Phase 10).
Implements the authoritative Best Score per Unique Question deduplication model
for overall points, category mastery, and skill tiers.
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Max
from .models import (
    AssessmentAttempt,
    AttemptStatus,
    QuestionType,
    Category,
    MCQAnswer,
)


def get_skill_tier(score: float):
    """
    Returns the student skill tier and UI badge class based on cumulative points.
    - 0-49 pts: Novice
    - 50-149 pts: Apprentice
    - 150-299 pts: Specialist
    - 300+ pts: Master
    """
    if score >= 300:
        return "Master", "bg-danger"
    elif score >= 150:
        return "Specialist", "bg-warning text-dark"
    elif score >= 50:
        return "Apprentice", "bg-info text-dark"
    else:
        return "Novice", "bg-secondary"


def compute_student_progress_and_mastery(user=None, session_id=None, timeframe='all_time', category_filter=None):
    """
    Computes unified points, theory/code split, and category mastery
    using the approved BEST SCORE PER UNIQUE QUESTION deduplication model.
    Repeated attempts on the same question never duplicate points.
    """
    if user and user.is_authenticated:
        attempts_qs = AssessmentAttempt.objects.filter(user=user, status=AttemptStatus.COMPLETED)
    elif session_id:
        attempts_qs = AssessmentAttempt.objects.filter(
            user__isnull=True, session_id=session_id, status=AttemptStatus.COMPLETED
        )
    else:
        attempts_qs = AssessmentAttempt.objects.none()

    # Timeframe filter
    now = timezone.now()
    if timeframe == 'month':
        attempts_qs = attempts_qs.filter(submitted_at__gte=now - timedelta(days=30))
    elif timeframe == 'week':
        attempts_qs = attempts_qs.filter(submitted_at__gte=now - timedelta(days=7))

    if category_filter and category_filter.lower() != 'all':
        attempts_qs = attempts_qs.filter(category__iexact=category_filter)

    attempts = list(attempts_qs.prefetch_related('questions', 'mcq_answers__question'))

    # Dictionary: question_id -> { 'best_marks': float, 'max_marks': int, 'category': str, 'type': str }
    best_per_question = {}

    for att in attempts:
        if att.question_type == QuestionType.CODE:
            q = att.questions.first()
            if q:
                res = getattr(att, 'result', None)
                obtained = float(res.obtained_marks) if res else float(att.total_score)
                max_m = int(q.marks) if q.marks else int(att.max_score or 10)
                if q.id not in best_per_question or obtained > best_per_question[q.id]['best_marks']:
                    best_per_question[q.id] = {
                        'best_marks': obtained,
                        'max_marks': max_m,
                        'category': q.category,
                        'type': QuestionType.CODE
                    }
        else:
            # MCQ attempt: questions scored per answer in MCQAnswer
            mcq_answers = list(att.mcq_answers.all())
            if mcq_answers:
                for ans in mcq_answers:
                    q = ans.question
                    if not q:
                        continue
                    obtained = float(ans.marks_obtained)
                    max_m = int(q.marks) if q.marks else 1
                    if q.id not in best_per_question or obtained > best_per_question[q.id]['best_marks']:
                        best_per_question[q.id] = {
                            'best_marks': obtained,
                            'max_marks': max_m,
                            'category': q.category,
                            'type': QuestionType.MCQ
                        }
            else:
                # Direct questions on attempt (fallback for direct/test creation)
                res = getattr(att, 'result', None)
                obtained = float(res.obtained_marks) if res else float(att.total_score)
                for q in att.questions.all():
                    max_m = int(q.marks) if q.marks else int(att.max_score or 1)
                    if q.id not in best_per_question or obtained > best_per_question[q.id]['best_marks']:
                        best_per_question[q.id] = {
                            'best_marks': obtained,
                            'max_marks': max_m,
                            'category': q.category,
                            'type': QuestionType.MCQ
                        }

    theory_score = sum(item['best_marks'] for item in best_per_question.values() if item['type'] == QuestionType.MCQ)
    coding_score = sum(item['best_marks'] for item in best_per_question.values() if item['type'] == QuestionType.CODE)
    unified_score = round(theory_score + coding_score, 1)

    skill_tier, skill_badge = get_skill_tier(unified_score)

    # Category Mastery (Best score per unique question in category / sum of max marks)
    category_buckets = {}
    for item in best_per_question.values():
        cat = item['category']
        if cat not in category_buckets:
            category_buckets[cat] = {
                'category': cat,
                'type': item['type'],
                'sum_best_marks': 0.0,
                'sum_max_marks': 0,
                'unique_questions': 0
            }
        category_buckets[cat]['sum_best_marks'] += item['best_marks']
        category_buckets[cat]['sum_max_marks'] += item['max_marks']
        category_buckets[cat]['unique_questions'] += 1

    category_mastery = []
    for cat, data in category_buckets.items():
        if data['sum_max_marks'] > 0:
            pct = round((data['sum_best_marks'] / data['sum_max_marks']) * 100, 1)
        else:
            pct = 0.0

        if pct >= 80.0:
            status_desc = "Mastered"
            status_badge = "bg-success"
        elif pct >= 50.0:
            status_desc = "Proficient"
            status_badge = "bg-info"
        else:
            status_desc = "Needs Practice"
            status_badge = "bg-warning text-dark"

        category_mastery.append({
            "category": cat,
            "type": data['type'],
            "mastery_percentage": pct,
            "status": status_desc,
            "status_badge": status_badge,
            "unique_questions": data['unique_questions'],
            "best_marks": round(data['sum_best_marks'], 1),
            "best_obtained_marks": round(data['sum_best_marks'], 1),
            "max_marks": data['sum_max_marks'],
            "max_available_marks": data['sum_max_marks'],
        })

    # Sort category mastery: highest mastery first
    category_mastery.sort(key=lambda x: -x['mastery_percentage'])

    return {
        "unified_score": unified_score,
        "theory_score": round(theory_score, 1),
        "coding_score": round(coding_score, 1),
        "unique_questions_count": len(best_per_question),
        "skill_tier": skill_tier,
        "skill_badge_class": skill_badge,
        "category_mastery": category_mastery,
    }

