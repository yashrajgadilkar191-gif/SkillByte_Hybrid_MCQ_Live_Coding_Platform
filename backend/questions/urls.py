"""
URL routes for Question Bank API.
"""

from django.urls import path
from .views import (
    QuestionListView,
    QuestionDetailView,
    AdminQuestionListView,
    AdminQuestionDetailView,
    AdminMCQCreateView,
    AdminMCQUpdateView,
    AdminCodingCreateView,
    AdminCodingUpdateView,
    AdminQuestionToggleActiveView,
    AdminQuestionDeleteView,
    AdminTestCaseCreateView,
    AdminTestCaseDetailView,
)
from .leaderboard_views import LeaderboardView
from .analytics_views import AdminAnalyticsView

urlpatterns = [
    # Phase 10: Leaderboard & Analytics endpoints
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),

    # Student / Public read-only endpoints
    path('', QuestionListView.as_view(), name='question_list'),
    path('<int:pk>/', QuestionDetailView.as_view(), name='question_detail'),

    # Phase 9: Admin Question Bank endpoints
    path('admin/', AdminQuestionListView.as_view(), name='admin_question_list'),
    path('admin/<int:pk>/', AdminQuestionDetailView.as_view(), name='admin_question_detail'),
    path('admin/mcq/', AdminMCQCreateView.as_view(), name='admin_mcq_create'),
    path('admin/mcq/<int:pk>/', AdminMCQUpdateView.as_view(), name='admin_mcq_update'),
    path('admin/code/', AdminCodingCreateView.as_view(), name='admin_code_create'),
    path('admin/code/<int:pk>/', AdminCodingUpdateView.as_view(), name='admin_code_update'),
    path('admin/<int:pk>/toggle-active/', AdminQuestionToggleActiveView.as_view(), name='admin_question_toggle_active'),
    path('admin/<int:pk>/delete/', AdminQuestionDeleteView.as_view(), name='admin_question_delete'),

    # Phase 9: Admin Test Case management endpoints
    path('admin/<int:question_id>/test-cases/', AdminTestCaseCreateView.as_view(), name='admin_test_case_create'),
    path('admin/test-cases/<int:pk>/', AdminTestCaseDetailView.as_view(), name='admin_test_case_detail'),
]


