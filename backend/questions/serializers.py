"""
Serializers for SKILLBYTE Question Bank & Assessments (Phase 3).
Strict security: NEVER expose is_correct or hidden test cases in student serializers.
"""

from rest_framework import serializers
from .models import (
    Question,
    QuestionOption,
    TestCase,
    AssessmentAttempt,
    MCQAnswer,
    CodingSubmission,
    AssessmentResult,
)


class QuestionOptionStudentSerializer(serializers.ModelSerializer):
    """
    Student-facing MCQ option serializer.
    STRICT SECURITY: 'is_correct' is strictly omitted.
    """
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_key', 'option_text']


class TestCaseStudentSerializer(serializers.ModelSerializer):
    """
    Student-facing test case serializer.
    STRICT SECURITY: Only sample (is_hidden=False) test cases are returned.
    """
    class Meta:
        model = TestCase
        fields = ['id', 'input_data', 'expected_output', 'marks']


class QuestionStudentListSerializer(serializers.ModelSerializer):
    """
    Lightweight list representation for students.
    """
    type = serializers.CharField(source='question_type')
    subject = serializers.CharField(source='category')

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'type',
            'subject',
            'difficulty',
            'marks',
            'time_limit'
        ]


class QuestionStudentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed student-facing representation of a Question.
    Omits correct answers and hidden test cases.
    """
    type = serializers.CharField(source='question_type')
    subject = serializers.CharField(source='category')
    options = serializers.SerializerMethodField()
    sample_test_cases = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'description',
            'type',
            'subject',
            'difficulty',
            'marks',
            'time_limit',
            'memory_limit',
            'input_format',
            'output_format',
            'constraints',
            'sample_input',
            'sample_output',
            'starter_code',
            'options',
            'sample_test_cases',
        ]

    def get_options(self, obj):
        if obj.question_type == 'MCQ':
            return QuestionOptionStudentSerializer(obj.options.all(), many=True).data
        return []

    def get_sample_test_cases(self, obj):
        if obj.question_type == 'CODE':
            sample_cases = obj.test_cases.filter(is_hidden=False)
            return TestCaseStudentSerializer(sample_cases, many=True).data
        return []


# Admin-Only Serializers (used exclusively by authenticated administrators)
class QuestionOptionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_key', 'option_text', 'is_correct', 'created_at']
        read_only_fields = ['id', 'created_at']


class TestCaseAdminSerializer(serializers.ModelSerializer):
    weight = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = ['id', 'question', 'input_data', 'expected_output', 'is_hidden', 'marks', 'weight', 'time_limit', 'memory_limit', 'created_at']
        read_only_fields = ['id', 'question', 'created_at']

    def get_weight(self, obj):
        return float(obj.marks)



class QuestionAdminListSerializer(serializers.ModelSerializer):
    """
    Detailed list view for administrators with options and test case counts.
    """
    options_count = serializers.SerializerMethodField()
    sample_test_cases_count = serializers.SerializerMethodField()
    hidden_test_cases_count = serializers.SerializerMethodField()
    total_test_cases_count = serializers.SerializerMethodField()
    has_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'description',
            'question_type',
            'category',
            'difficulty',
            'marks',
            'time_limit',
            'memory_limit',
            'is_active',
            'created_at',
            'updated_at',
            'options_count',
            'sample_test_cases_count',
            'hidden_test_cases_count',
            'total_test_cases_count',
            'has_attempts',
        ]

    def get_options_count(self, obj):
        return obj.options.count() if obj.question_type == 'MCQ' else 0

    def get_sample_test_cases_count(self, obj):
        return obj.test_cases.filter(is_hidden=False).count() if obj.question_type == 'CODE' else 0

    def get_hidden_test_cases_count(self, obj):
        return obj.test_cases.filter(is_hidden=True).count() if obj.question_type == 'CODE' else 0

    def get_total_test_cases_count(self, obj):
        return obj.test_cases.count() if obj.question_type == 'CODE' else 0

    def get_has_attempts(self, obj):
        return obj.assessment_attempts_set.exists() or obj.coding_submissions.exists()


class QuestionAdminDetailSerializer(serializers.ModelSerializer):
    options = QuestionOptionAdminSerializer(many=True, read_only=True)
    test_cases = TestCaseAdminSerializer(many=True, read_only=True)
    has_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = '__all__'

    def get_has_attempts(self, obj):
        return obj.assessment_attempts_set.exists() or obj.coding_submissions.exists()


class MCQOptionInputSerializer(serializers.Serializer):
    option_key = serializers.CharField(max_length=10, required=True)
    option_text = serializers.CharField(required=True)
    is_correct = serializers.BooleanField(default=False)

    def validate_option_key(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Option key cannot be empty.")
        return value.strip().upper()

    def validate_option_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Option text cannot be empty.")
        return value.strip()


class MCQQuestionCreateUpdateSerializer(serializers.ModelSerializer):
    options = MCQOptionInputSerializer(many=True, required=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'description',
            'category',
            'difficulty',
            'marks',
            'time_limit',
            'explanation',
            'is_active',
            'options',
        ]
        read_only_fields = ['id']

    def validate_category(self, value):
        valid_mcq_categories = ['General Knowledge', 'English', 'Mathematics']
        if value not in valid_mcq_categories:
            raise serializers.ValidationError(
                f"Invalid MCQ category '{value}'. Allowed categories: {', '.join(valid_mcq_categories)}."
            )
        return value

    def validate_marks(self, value):
        if value <= 0:
            raise serializers.ValidationError("Marks must be greater than zero.")
        return value

    def validate_time_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time limit must be greater than zero seconds.")
        return value

    def validate_options(self, options):
        if not options or len(options) < 2:
            raise serializers.ValidationError("MCQ must have at least 2 options.")

        # Check unique option keys
        keys = [opt['option_key'] for opt in options]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("Option keys (e.g. A, B, C, D) must be unique.")

        # Check exactly one correct option
        correct_count = sum(1 for opt in options if opt.get('is_correct'))
        if correct_count != 1:
            raise serializers.ValidationError(
                f"Exactly one option must be marked as correct. Found: {correct_count} correct options."
            )

        return options

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        validated_data['question_type'] = 'MCQ'
        question = Question.objects.create(**validated_data)

        for opt in options_data:
            QuestionOption.objects.create(
                question=question,
                option_key=opt['option_key'],
                option_text=opt['option_text'],
                is_correct=opt['is_correct']
            )

        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.question_type = 'MCQ'
        instance.save()

        if options_data is not None:
            # Replace existing options
            instance.options.all().delete()
            for opt in options_data:
                QuestionOption.objects.create(
                    question=instance,
                    option_key=opt['option_key'],
                    option_text=opt['option_text'],
                    is_correct=opt['is_correct']
                )

        return instance


class CodingQuestionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'description',
            'category',
            'difficulty',
            'marks',
            'time_limit',
            'memory_limit',
            'input_format',
            'output_format',
            'constraints',
            'sample_input',
            'sample_output',
            'starter_code',
            'explanation',
            'is_active',
        ]
        read_only_fields = ['id']

    def validate_category(self, value):
        valid_coding_categories = ['Python', 'Java', 'C++', 'DSA']
        if value not in valid_coding_categories:
            raise serializers.ValidationError(
                f"Invalid Coding category '{value}'. Allowed categories: {', '.join(valid_coding_categories)}."
            )
        return value

    def validate_marks(self, value):
        if value <= 0:
            raise serializers.ValidationError("Marks must be greater than zero.")
        return value

    def validate_time_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time limit must be greater than zero seconds.")
        return value

    def validate_memory_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Memory limit must be greater than zero MB.")
        return value

    def create(self, validated_data):
        validated_data['question_type'] = 'CODE'
        return Question.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.question_type = 'CODE'
        instance.save()
        return instance


class TestCaseCreateUpdateSerializer(serializers.ModelSerializer):
    weight = serializers.FloatField(required=False, write_only=True)

    class Meta:
        model = TestCase
        fields = [
            'id',
            'input_data',
            'expected_output',
            'is_hidden',
            'marks',
            'weight',
            'time_limit',
            'memory_limit',
        ]
        read_only_fields = ['id']

    def validate_input_data(self, value):
        if value is None:
            raise serializers.ValidationError("Input data cannot be null.")
        return value

    def validate_expected_output(self, value):
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Expected output cannot be empty.")
        return value

    def validate_marks(self, value):
        if value <= 0:
            raise serializers.ValidationError("Marks must be greater than zero.")
        return value

    def validate_time_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time limit must be greater than zero seconds.")
        return value

    def validate_memory_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Memory limit must be greater than zero MB.")
        return value

    def create(self, validated_data):
        weight = validated_data.pop('weight', None)
        if weight is not None and 'marks' not in validated_data:
            validated_data['marks'] = max(1, int(round(weight)))
        if 'question' not in validated_data and 'question' in self.context:
            validated_data['question'] = self.context['question']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        weight = validated_data.pop('weight', None)
        if weight is not None and 'marks' not in validated_data:
            validated_data['marks'] = max(1, int(round(weight)))
        return super().update(instance, validated_data)


