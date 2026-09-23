"""
Core Database Models for SKILLBYTE Question Bank & Assessments Foundation (Phase 3).
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class QuestionType(models.TextChoices):
    MCQ = 'MCQ', _('Multiple Choice Question')
    CODE = 'CODE', _('Coding Problem')


class DifficultyLevel(models.TextChoices):
    EASY = 'EASY', _('Easy')
    MEDIUM = 'MEDIUM', _('Medium')
    HARD = 'HARD', _('Hard')


class Category(models.TextChoices):
    # Theoretical MCQ Subjects
    GENERAL_KNOWLEDGE = 'General Knowledge', _('General Knowledge')
    ENGLISH = 'English', _('English')
    MATHEMATICS = 'Mathematics', _('Mathematics')

    # Practical Coding Categories
    PYTHON = 'Python', _('Python')
    JAVA = 'Java', _('Java')
    CPP = 'C++', _('C++')
    DSA = 'DSA', _('Data Structures & Algorithms')


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
    COMPLETED = 'COMPLETED', _('Completed')
    ABANDONED = 'ABANDONED', _('Abandoned')


class SubmissionStatus(models.TextChoices):
    ACCEPTED = 'ACCEPTED', _('Accepted')
    PARTIAL = 'PARTIAL', _('Partial Credit')
    WRONG_ANSWER = 'WRONG_ANSWER', _('Wrong Answer')
    COMPILATION_ERROR = 'COMPILATION_ERROR', _('Compilation Error')
    RUNTIME_ERROR = 'RUNTIME_ERROR', _('Runtime Error')
    TIME_LIMIT_EXCEEDED = 'TIME_LIMIT_EXCEEDED', _('Time Limit Exceeded')
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE', _('Service Unavailable')
    PENDING = 'PENDING', _('Pending')


class Question(models.Model):
    """
    Unified Question model supporting both MCQ theoretical questions and Coding problems.
    """
    title = models.CharField(max_length=255, verbose_name=_('Title'), db_index=True)
    description = models.TextField(verbose_name=_('Description / Problem Statement'))
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
        verbose_name=_('Question Type'),
        db_index=True
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        verbose_name=_('Subject / Category'),
        db_index=True
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.EASY,
        verbose_name=_('Difficulty Level'),
        db_index=True
    )
    marks = models.PositiveIntegerField(default=1, verbose_name=_('Marks / Weight'))

    # Time & Resource Limits
    time_limit = models.PositiveIntegerField(
        default=60,
        help_text=_('For MCQ: countdown in seconds. For Coding: execution time limit in seconds.')
    )
    memory_limit = models.PositiveIntegerField(
        default=256,
        help_text=_('Memory limit in MB (applies to coding execution).')
    )

    # Coding Specific Specifications
    input_format = models.TextField(blank=True, default='', verbose_name=_('Input Format'))
    output_format = models.TextField(blank=True, default='', verbose_name=_('Output Format'))
    constraints = models.TextField(blank=True, default='', verbose_name=_('Constraints'))
    sample_input = models.TextField(blank=True, default='', verbose_name=_('Sample Input'))
    sample_output = models.TextField(blank=True, default='', verbose_name=_('Sample Output'))
    starter_code = models.JSONField(
        blank=True,
        default=dict,
        help_text=_('JSON map of language templates: {"python": "...", "java": "...", "cpp": "..."}')
    )
    explanation = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Explanation / Solution Notes'),
        help_text=_('Explanation revealed after assessment completion.')
    )

    # Lifecycle & Audit
    is_active = models.BooleanField(default=True, verbose_name=_('Active Status'), db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_questions',
        verbose_name=_('Created By')
    )

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['category', 'difficulty', '-created_at']

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.title} ({self.get_difficulty_display()})"

    def clean(self):
        # Validate that category aligns with question type
        mcq_categories = [
            Category.GENERAL_KNOWLEDGE,
            Category.ENGLISH,
            Category.MATHEMATICS
        ]
        coding_categories = [
            Category.PYTHON,
            Category.JAVA,
            Category.CPP,
            Category.DSA
        ]

        if self.question_type == QuestionType.MCQ and self.category not in mcq_categories:
            raise ValidationError({
                'category': _('Category must be General Knowledge, English, or Mathematics for MCQ questions.')
            })
        elif self.question_type == QuestionType.CODE and self.category not in coding_categories:
            raise ValidationError({
                'category': _('Category must be Python, Java, C++, or DSA for Coding problems.')
            })


class QuestionOption(models.Model):
    """
    Options for Multiple Choice Questions.
    Security: is_correct must NEVER be exposed in student-facing APIs.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('Question')
    )
    option_key = models.CharField(max_length=10, verbose_name=_('Option Key (e.g. A, B, C, D)'))
    option_text = models.TextField(verbose_name=_('Option Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct Answer'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('MCQ Option')
        verbose_name_plural = _('MCQ Options')
        unique_together = ('question', 'option_key')
        ordering = ['question', 'option_key']

    def __str__(self):
        correct_tag = " [CORRECT]" if self.is_correct else ""
        return f"{self.question.title} — Option {self.option_key}{correct_tag}"

    def clean(self):
        if self.question and self.question.question_type != QuestionType.MCQ:
            raise ValidationError(_('Options can only belong to MCQ questions.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TestCase(models.Model):
    """
    Test cases for live coding evaluation.
    Security: Hidden test cases (is_hidden=True) must NEVER be exposed to students.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name=_('Coding Problem')
    )
    input_data = models.TextField(verbose_name=_('Input Data / Stdin'))
    expected_output = models.TextField(verbose_name=_('Expected Output / Stdout'))
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_('Is Hidden Test Case'),
        help_text=_('If True, this test case is used for hidden grading and never displayed to students.')
    )
    marks = models.PositiveIntegerField(default=1, verbose_name=_('Marks / Weight'))
    time_limit = models.FloatField(default=2.0, verbose_name=_('Time Limit (seconds)'))
    memory_limit = models.PositiveIntegerField(default=256, verbose_name=_('Memory Limit (MB)'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Test Case')
        verbose_name_plural = _('Test Cases')
        ordering = ['question', 'is_hidden', 'id']

    def __str__(self):
        visibility = "Hidden" if self.is_hidden else "Sample"
        return f"{self.question.title} — {visibility} Test Case #{self.id or 'New'}"

    def clean(self):
        if self.question and self.question.question_type != QuestionType.CODE:
            raise ValidationError(_('Test cases can only belong to Coding problems.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class AssessmentAttempt(models.Model):
    """
    Represents an assessment session initiated by a student or a guest.
    Guest attempts: user is null, session_id is populated.
    Student attempts: user is associated.
    """
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assessment_attempts',
        verbose_name=_('Student User')
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        verbose_name=_('Guest Session Identifier')
    )
    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        verbose_name=_('Assessment Type')
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        verbose_name=_('Subject / Category')
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.EASY,
        verbose_name=_('Difficulty Level')
    )
    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
        verbose_name=_('Attempt Status')
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Submitted At'))
    total_score = models.FloatField(default=0.0, verbose_name=_('Total Score'))
    max_score = models.PositiveIntegerField(default=0, verbose_name=_('Maximum Score'))
    time_limit_seconds = models.PositiveIntegerField(
        default=600,
        verbose_name=_('Time Limit (seconds)'),
        help_text=_('Total duration allocated for this assessment attempt in seconds.')
    )
    language = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name=_('Selected Language')
    )
    questions = models.ManyToManyField(
        Question,
        blank=True,
        related_name='assessment_attempts_set',
        verbose_name=_('Selected Questions')
    )

    class Meta:
        verbose_name = _('Assessment Attempt')
        verbose_name_plural = _('Assessment Attempts')
        ordering = ['-started_at']

    def __str__(self):
        actor = self.user.username if self.user else f"Guest ({self.session_id or 'anon'})"
        return f"{actor} — {self.category} ({self.get_status_display()})"

    @property
    def is_guest(self):
        return self.user is None

    @property
    def is_time_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        if self.time_limit_seconds and self.started_at:
            return timezone.now() > self.started_at + timedelta(seconds=self.time_limit_seconds)
        return False


class MCQAnswer(models.Model):
    """
    Records an answer chosen during an MCQ assessment attempt.
    """
    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='mcq_answers',
        verbose_name=_('Attempt')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='mcq_answers',
        verbose_name=_('Question')
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Selected Option')
    )
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    marks_obtained = models.FloatField(default=0.0, verbose_name=_('Marks Obtained'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Answered At'))

    class Meta:
        verbose_name = _('MCQ Answer')
        verbose_name_plural = _('MCQ Answers')
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"Attempt #{self.attempt.id} — Question #{self.question.id}"


class CodingSubmission(models.Model):
    """
    Foundation model for coding submissions (supports Judge0 tokens, test case verdicts, and failure reasons).
    """
    attempt = models.ForeignKey(
        AssessmentAttempt,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='coding_submissions',
        verbose_name=_('Assessment Attempt')
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='coding_submissions',
        verbose_name=_('Student User')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='coding_submissions',
        verbose_name=_('Coding Problem')
    )
    language = models.CharField(max_length=30, verbose_name=_('Programming Language'))
    source_code = models.TextField(verbose_name=_('Source Code'))
    judge0_token = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Judge0 Token'))
    status = models.CharField(
        max_length=30,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
        verbose_name=_('Submission Status'),
        db_index=True
    )
    score = models.FloatField(default=0.0, verbose_name=_('Score / Partial Credit'))
    passed_test_cases = models.PositiveIntegerField(default=0, verbose_name=_('Passed Test Cases'))
    total_test_cases = models.PositiveIntegerField(default=0, verbose_name=_('Total Test Cases'))
    execution_time = models.FloatField(null=True, blank=True, verbose_name=_('Execution Time (seconds)'))
    memory_usage = models.FloatField(null=True, blank=True, verbose_name=_('Memory Usage (KB)'))
    error_output = models.TextField(blank=True, default='', verbose_name=_('Compiler / Runtime Output'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Submitted At'))

    class Meta:
        verbose_name = _('Coding Submission')
        verbose_name_plural = _('Coding Submissions')
        ordering = ['-created_at']

    def __str__(self):
        user_name = self.user.username if self.user else "Guest"
        return f"{user_name} — {self.question.title} ({self.get_status_display()})"


class AssessmentResult(models.Model):
    """
    Result summary for an assessment attempt.
    """
    attempt = models.OneToOneField(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name=_('Assessment Attempt')
    )
    total_marks = models.PositiveIntegerField(default=0, verbose_name=_('Total Marks'))
    obtained_marks = models.FloatField(default=0.0, verbose_name=_('Obtained Marks'))
    percentage = models.FloatField(default=0.0, verbose_name=_('Percentage Score'))
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Completed At'))

    class Meta:
        verbose_name = _('Assessment Result')
        verbose_name_plural = _('Assessment Results')

    def __str__(self):
        return f"Result for Attempt #{self.attempt.id}: {self.obtained_marks}/{self.total_marks} ({self.percentage}%)"

