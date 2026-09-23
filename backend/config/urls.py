"""
URL configuration for SKILLBYTE project.
"""

from django.contrib import admin
from django.urls import path, include
from api.views import (
    index_view,
    login_page_view,
    register_page_view,
    dashboard_page_view,
    mcq_setup_page_view,
    mcq_assessment_page_view,
    mcq_result_page_view,
    coding_list_page_view,
    coding_setup_page_view,
    coding_assessment_page_view,
    coding_result_page_view,
    attempts_page_view,
    admin_question_bank_page_view,
    leaderboard_page_view,
    admin_analytics_page_view,
)
from questions.leaderboard_views import LeaderboardView
from questions.analytics_views import AdminAnalyticsView

urlpatterns = [
    path('admin/questions/', admin_question_bank_page_view, name='admin_question_bank_page'),
    path('admin/analytics/', admin_analytics_page_view, name='admin_analytics_page'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/questions/', include('questions.urls')),
    path('api/assessments/', include('questions.assessment_urls')),
    path('api/leaderboard/', LeaderboardView.as_view(), name='api_leaderboard'),
    path('api/admin/analytics/', AdminAnalyticsView.as_view(), name='api_admin_analytics'),
    path('api/', include('api.urls')),
    path('', index_view, name='home'),
    path('login/', login_page_view, name='login'),
    path('register/', register_page_view, name='register'),
    path('dashboard/', dashboard_page_view, name='dashboard'),
    path('leaderboard/', leaderboard_page_view, name='leaderboard_page'),
    path('attempts/', attempts_page_view, name='my_attempts_page'),
    path('assessments/history/', attempts_page_view),
    path('assessments/mcq/', mcq_setup_page_view, name='mcq_setup_page'),
    path('assessments/mcq/<int:attempt_id>/', mcq_assessment_page_view, name='mcq_assessment_page'),
    path('assessments/mcq/<int:attempt_id>/result/', mcq_result_page_view, name='mcq_result_page'),
    # Live Coding Assessment (Phase 5)
    path('coding/', coding_list_page_view, name='coding_list_page'),
    path('coding/setup/', coding_setup_page_view, name='coding_setup_page'),
    path('coding/assessment/<int:attempt_id>/', coding_assessment_page_view, name='coding_assessment_page'),
    path('coding/result/<int:attempt_id>/', coding_result_page_view, name='coding_result_page'),
    # Aliases
    path('assessments/coding/', coding_setup_page_view),
    path('assessments/coding/<int:attempt_id>/', coding_assessment_page_view),
    path('assessments/coding/<int:attempt_id>/result/', coding_result_page_view),
]

from django.conf import settings
from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
]

