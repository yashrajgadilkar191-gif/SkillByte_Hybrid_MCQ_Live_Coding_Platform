"""
Django Admin integration for SkillByte Question Bank & Assessments (Phase 3).
"""

from django.contrib import admin
from .models import (
    Question,
    QuestionOption,
    TestCase,
    AssessmentAttempt,
    MCQAnswer,
    CodingSubmission,
    AssessmentResult,
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    fields = ('option_key', 'option_text', 'is_correct')


class TestCaseInline(admin.StackedInline):
    model = TestCase
    extra = 2
    fields = ('input_data', 'expected_output', 'is_hidden', 'marks', 'time_limit', 'memory_limit')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'question_type', 'category', 'difficulty', 'marks', 'is_active', 'created_at')
    list_filter = ('question_type', 'category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    inlines = [QuestionOptionInline, TestCaseInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option_key', 'option_text', 'is_correct')
    list_filter = ('is_correct', 'question__category')
    search_fields = ('option_text', 'question__title')


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'is_hidden', 'marks', 'time_limit', 'memory_limit')
    list_filter = ('is_hidden', 'question__category')
    search_fields = ('question__title',)


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'question_type', 'category', 'difficulty', 'status', 'total_score', 'started_at')
    list_filter = ('status', 'question_type', 'category', 'difficulty')
    search_fields = ('user__username', 'session_id')


@admin.register(MCQAnswer)
class MCQAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_option', 'is_correct', 'marks_obtained')
    list_filter = ('is_correct',)


@admin.register(CodingSubmission)
class CodingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'language', 'status', 'passed_test_cases', 'total_test_cases', 'score', 'created_at')
    list_filter = ('status', 'language', 'question__category')
    search_fields = ('user__username', 'question__title')


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'obtained_marks', 'total_marks', 'percentage', 'completed_at')

