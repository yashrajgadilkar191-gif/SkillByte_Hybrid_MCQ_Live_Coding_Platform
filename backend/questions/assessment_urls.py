"""
URL routes for SkillByte Assessments API (Phase 4).
"""

from django.urls import path
from .assessment_views import (
    MCQAssessmentStartView,
    MCQAssessmentAnswerView,
    MCQAssessmentSubmitView,
    MCQAssessmentResultView,
    CodingAssessmentStartView,
    CodingAssessmentDetailView,
    CodingAssessmentRunCodeView,
    CodingAssessmentSubmitView,
    CodingAssessmentResultView,
    MyAssessmentAttemptsView,
    AssessmentProgressView,
    AssessmentAbandonView,
    ActiveAssessmentAttemptView,
)

urlpatterns = [
    # Assessment Resumption & Lifecycle (Phase 11)
    path('active/', ActiveAssessmentAttemptView.as_view(), name='assessment_active'),
    path('<int:attempt_id>/abandon/', AssessmentAbandonView.as_view(), name='assessment_abandon'),

    # MCQ Assessment
    path('mcq/start/', MCQAssessmentStartView.as_view(), name='mcq_start'),
    path('mcq/<int:attempt_id>/answer/', MCQAssessmentAnswerView.as_view(), name='mcq_answer'),
    path('mcq/<int:attempt_id>/submit/', MCQAssessmentSubmitView.as_view(), name='mcq_submit'),
    path('mcq/<int:attempt_id>/result/', MCQAssessmentResultView.as_view(), name='mcq_result'),

    # Live Coding Assessment (Phase 5, 6 & 10)
    path('coding/start/', CodingAssessmentStartView.as_view(), name='coding_start'),
    path('coding/<int:attempt_id>/', CodingAssessmentDetailView.as_view(), name='coding_detail'),
    path('coding/<int:attempt_id>/run/', CodingAssessmentRunCodeView.as_view(), name='coding_run'),
    path('coding/<int:attempt_id>/submit/', CodingAssessmentSubmitView.as_view(), name='coding_submit'),
    path('coding/<int:attempt_id>/result/', CodingAssessmentResultView.as_view(), name='coding_result'),

    # Student Attempts History & Progress
    path('my-attempts/', MyAssessmentAttemptsView.as_view(), name='my_attempts'),
    path('progress/', AssessmentProgressView.as_view(), name='assessment_progress'),
    path('my-progress/', AssessmentProgressView.as_view(), name='my_assessment_progress'),
]

