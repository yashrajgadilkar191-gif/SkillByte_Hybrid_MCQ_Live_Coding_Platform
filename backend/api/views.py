"""
API Views for SKILLBYTE project.
"""

from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for verifying backend and DRF connectivity.
    Expected response:
    {
        "status": "ok",
        "service": "SkillByte API"
    }
    """
    return Response({
        "status": "ok",
        "service": "SkillByte API"
    })


def index_view(request):
    """
    Serves the foundational frontend template in Django's monolithic architecture.
    """
    return render(request, 'index.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def login_page_view(request):
    """
    Serves the login page.
    """
    return render(request, 'login.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def register_page_view(request):
    """
    Serves the registration page.
    """
    return render(request, 'register.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def dashboard_page_view(request):
    """
    Serves the dashboard placeholder page.
    """
    return render(request, 'dashboard.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def mcq_setup_page_view(request):
    """
    Serves the MCQ Assessment setup/selection page.
    """
    return render(request, 'assessments/mcq_setup.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def mcq_assessment_page_view(request, attempt_id):
    """
    Serves the active MCQ live assessment screen.
    """
    return render(request, 'assessments/mcq_assessment.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
        'attempt_id': attempt_id,
    })


def mcq_result_page_view(request, attempt_id):
    """
    Serves the completed MCQ assessment results page.
    """
    return render(request, 'assessments/mcq_result.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
        'attempt_id': attempt_id,
    })


def coding_list_page_view(request):
    """
    Serves the Coding Problems directory/list page.
    """
    return render(request, 'coding/coding_list.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def coding_setup_page_view(request):
    """
    Serves the Live Coding assessment configuration/setup page.
    """
    return render(request, 'assessments/coding_setup.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def coding_assessment_page_view(request, attempt_id):
    """
    Serves the Live Coding assessment workspace page with Monaco Editor.
    """
    return render(request, 'assessments/coding_assessment.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
        'attempt_id': attempt_id,
    })


def coding_result_page_view(request, attempt_id):
    """
    Serves the completed Live Coding assessment results page.
    """
    return render(request, 'assessments/coding_result.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
        'attempt_id': attempt_id,
    })


def attempts_page_view(request):
    """
    Serves the student attempt history and progress tracking page (Phase 8).
    """
    return render(request, 'assessments/my_attempts.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def admin_question_bank_page_view(request):
    """
    Serves the Admin Question Bank & Test Case Management workspace page (Phase 9).
    Frontend verifies token and ADMIN role via auth.js and displays 403 access denial if unauthorized.
    """
    return render(request, 'admin/question_bank.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def leaderboard_page_view(request):
    """
    Serves the Student & Platform Leaderboard page (Phase 10).
    """
    return render(request, 'leaderboard.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def admin_analytics_page_view(request):
    """
    Serves the Admin Platform & Assessment Analytics dashboard (Phase 10).
    """
    return render(request, 'admin/analytics.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def profile_page_view(request):
    """
    Serves the Student Profile & Account Settings page (Phase 11).
    """
    return render(request, 'profile.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    })


def custom_404_view(request, exception=None):
    """
    Custom 404 Page Not Found error handler (Phase 11).
    """
    return render(request, '404.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    }, status=404)


def custom_403_view(request, exception=None):
    """
    Custom 403 Forbidden error handler (Phase 11).
    """
    return render(request, '403.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    }, status=403)


def custom_500_view(request):
    """
    Custom 500 Server Error handler (Phase 11).
    """
    return render(request, '500.html', {
        'platform_name': 'SKILLBYTE',
        'tagline': 'Where Theory Meets Practice',
    }, status=500)



