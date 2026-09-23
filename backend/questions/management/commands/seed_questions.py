"""
Management command to seed development questions and test cases (Phase 3).
Seeds:
- MCQ: General Knowledge, English, Mathematics (with 4 options each)
- Coding: Python, Java, C++, DSA (with sample test cases AND hidden test cases)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from questions.models import (
    Question,
    QuestionOption,
    TestCase,
    QuestionType,
    Category,
    DifficultyLevel,
)


class Command(BaseCommand):
    help = 'Seed development questions for MCQ and Coding (Phase 3).'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Seeding SkillByte Question Bank (Phase 3) ==="))

        # -------------------------------------------------------------
        # 1. MCQ QUESTIONS
        # -------------------------------------------------------------
        mcq_data = [
            # General Knowledge
            {
                "title": "Capital of France",
                "description": "What is the capital city of France?",
                "category": Category.GENERAL_KNOWLEDGE,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 45,
                "options": [
                    {"key": "A", "text": "Berlin", "correct": False},
                    {"key": "B", "text": "Madrid", "correct": False},
                    {"key": "C", "text": "Paris", "correct": True},
                    {"key": "D", "text": "Rome", "correct": False},
                ]
            },
            {
                "title": "Red Planet of the Solar System",
                "description": "Which celestial body in our solar system is widely nicknamed the 'Red Planet'?",
                "category": Category.GENERAL_KNOWLEDGE,
                "difficulty": DifficultyLevel.MEDIUM,
                "marks": 2,
                "time_limit": 60,
                "options": [
                    {"key": "A", "text": "Venus", "correct": False},
                    {"key": "B", "text": "Mars", "correct": True},
                    {"key": "C", "text": "Jupiter", "correct": False},
                    {"key": "D", "text": "Saturn", "correct": False},
                ]
            },

            {
                "title": "First Artificial Satellite in Space",
                "description": "Which nation launched the first artificial satellite, Sputnik 1, into orbit in 1957?",
                "category": Category.GENERAL_KNOWLEDGE,
                "difficulty": DifficultyLevel.HARD,
                "marks": 3,
                "time_limit": 60,
                "explanation": "Sputnik 1 was launched by the Soviet Union on October 4, 1957, ushering in the Space Age.",
                "options": [
                    {"key": "A", "text": "United States", "correct": False},
                    {"key": "B", "text": "Soviet Union", "correct": True},
                    {"key": "C", "text": "United Kingdom", "correct": False},
                    {"key": "D", "text": "Germany", "correct": False},
                ]
            },
            {
                "title": "Largest Ocean on Earth",
                "description": "Which of the following is the largest and deepest ocean on Earth?",
                "category": Category.GENERAL_KNOWLEDGE,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 45,
                "explanation": "The Pacific Ocean is the largest and deepest of Earth's oceanic divisions.",
                "options": [
                    {"key": "A", "text": "Atlantic Ocean", "correct": False},
                    {"key": "B", "text": "Indian Ocean", "correct": False},
                    {"key": "C", "text": "Pacific Ocean", "correct": True},
                    {"key": "D", "text": "Arctic Ocean", "correct": False},
                ]
            },

            # English
            {
                "title": "Synonym of 'Benevolent'",
                "description": "Select the word that is most nearly synonymous with 'Benevolent'.",
                "category": Category.ENGLISH,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 45,
                "explanation": "Benevolent means well-meaning and kindly.",
                "options": [
                    {"key": "A", "text": "Malevolent", "correct": False},
                    {"key": "B", "text": "Kind-hearted", "correct": True},
                    {"key": "C", "text": "Indifferent", "correct": False},
                    {"key": "D", "text": "Cruel", "correct": False},
                ]
            },
            {
                "title": "Antonym of 'Frugal'",
                "description": "Which word is the opposite (antonym) of 'Frugal'?",
                "category": Category.ENGLISH,
                "difficulty": DifficultyLevel.MEDIUM,
                "marks": 2,
                "time_limit": 60,
                "explanation": "Frugal means sparing or economical; extravagant is the opposite.",
                "options": [
                    {"key": "A", "text": "Economical", "correct": False},
                    {"key": "B", "text": "Extravagant", "correct": True},
                    {"key": "C", "text": "Thrifty", "correct": False},
                    {"key": "D", "text": "Miserly", "correct": False},
                ]
            },
            {
                "title": "Literary Device Identification",
                "description": "Identify the literary device used in: 'The wind whispered through the dark pines.'",
                "category": Category.ENGLISH,
                "difficulty": DifficultyLevel.HARD,
                "marks": 3,
                "time_limit": 60,
                "explanation": "Attributing human traits like whispering to non-human things like the wind is personification.",
                "options": [
                    {"key": "A", "text": "Simile", "correct": False},
                    {"key": "B", "text": "Personification", "correct": True},
                    {"key": "C", "text": "Hyperbole", "correct": False},
                    {"key": "D", "text": "Oxymoron", "correct": False},
                ]
            },
            {
                "title": "Antonym of 'Transparent'",
                "description": "Choose the word opposite in meaning to 'Transparent'.",
                "category": Category.ENGLISH,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 45,
                "explanation": "Opaque objects do not let light pass through, unlike transparent ones.",
                "options": [
                    {"key": "A", "text": "Translucent", "correct": False},
                    {"key": "B", "text": "Clear", "correct": False},
                    {"key": "C", "text": "Opaque", "correct": True},
                    {"key": "D", "text": "Luminous", "correct": False},
                ]
            },

            # Mathematics
            {
                "title": "Exponentiation: 2^5",
                "description": "What is the evaluated value of 2 raised to the 5th power (2^5)?",
                "category": Category.MATHEMATICS,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 60,
                "explanation": "2 * 2 * 2 * 2 * 2 = 32.",
                "options": [
                    {"key": "A", "text": "16", "correct": False},
                    {"key": "B", "text": "32", "correct": True},
                    {"key": "C", "text": "64", "correct": False},
                    {"key": "D", "text": "10", "correct": False},
                ]
            },
            {
                "title": "Linear Equation Solving",
                "description": "Solve for x in the equation: 3x - 7 = 14",
                "category": Category.MATHEMATICS,
                "difficulty": DifficultyLevel.MEDIUM,
                "marks": 2,
                "time_limit": 90,
                "explanation": "3x = 14 + 7 = 21 => x = 7.",
                "options": [
                    {"key": "A", "text": "x = 5", "correct": False},
                    {"key": "B", "text": "x = 6", "correct": False},
                    {"key": "C", "text": "x = 7", "correct": True},
                    {"key": "D", "text": "x = 8", "correct": False},
                ]
            },
            {
                "title": "Quadratic Equation Roots",
                "description": "Find the roots of the quadratic equation: x^2 - 5x + 6 = 0",
                "category": Category.MATHEMATICS,
                "difficulty": DifficultyLevel.HARD,
                "marks": 3,
                "time_limit": 90,
                "explanation": "(x - 2)(x - 3) = 0 => x = 2 and x = 3.",
                "options": [
                    {"key": "A", "text": "x = 1 and x = 6", "correct": False},
                    {"key": "B", "text": "x = 2 and x = 3", "correct": True},
                    {"key": "C", "text": "x = -2 and x = -3", "correct": False},
                    {"key": "D", "text": "x = -1 and x = -6", "correct": False},
                ]
            },
            {
                "title": "Square Root of 144",
                "description": "What is the principal square root of 144?",
                "category": Category.MATHEMATICS,
                "difficulty": DifficultyLevel.EASY,
                "marks": 1,
                "time_limit": 45,
                "explanation": "12 * 12 = 144.",
                "options": [
                    {"key": "A", "text": "11", "correct": False},
                    {"key": "B", "text": "12", "correct": True},
                    {"key": "C", "text": "14", "correct": False},
                    {"key": "D", "text": "16", "correct": False},
                ]
            },
        ]

        mcq_created = 0
        for item in mcq_data:
            q, created = Question.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "question_type": QuestionType.MCQ,
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "marks": item["marks"],
                    "time_limit": item["time_limit"],
                    "is_active": True,
                }
            )
            if created:
                mcq_created += 1
                for opt in item["options"]:
                    QuestionOption.objects.create(
                        question=q,
                        option_key=opt["key"],
                        option_text=opt["text"],
                        is_correct=opt["correct"],
                    )

        self.stdout.write(self.style.SUCCESS(f"MCQ Questions: {mcq_created} seeded."))

        # -------------------------------------------------------------
        # 2. CODING PROBLEMS (with Sample and Hidden Test Cases)
        # -------------------------------------------------------------
        coding_data = [
            # Python Coding Problem
            {
                "title": "Sum of Two Numbers",
                "description": "Read two integers from standard input and print their sum.",
                "category": Category.PYTHON,
                "difficulty": DifficultyLevel.EASY,
                "marks": 10,
                "time_limit": 2,
                "memory_limit": 128,
                "input_format": "Two space-separated integers a and b.",
                "output_format": "Single integer representing a + b.",
                "constraints": "-10^9 <= a, b <= 10^9",
                "sample_input": "3 5",
                "sample_output": "8",
                "starter_code": {
                    "python": "# Read input and print sum\na, b = map(int, input().split())\nprint(a + b)\n",
                    "java": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.println(a + b);\n    }\n}\n",
                    "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n    long long a, b;\n    if (cin >> a >> b) {\n        cout << a + b << endl;\n    }\n    return 0;\n}\n"
                },
                "test_cases": [
                    {"input": "3 5", "output": "8", "hidden": False, "marks": 4},
                    {"input": "100 250", "output": "350", "hidden": True, "marks": 3},
                    {"input": "-10 25", "output": "15", "hidden": True, "marks": 3},
                ]
            },

            # Java Coding Problem
            {
                "title": "Palindrome String Checker",
                "description": "Given a string S, print 'YES' if it is a palindrome, or 'NO' otherwise.",
                "category": Category.JAVA,
                "difficulty": DifficultyLevel.EASY,
                "marks": 15,
                "time_limit": 2,
                "memory_limit": 256,
                "input_format": "A single line containing string S.",
                "output_format": "Print 'YES' or 'NO' (case-sensitive).",
                "constraints": "1 <= length(S) <= 10^5",
                "sample_input": "racecar",
                "sample_output": "YES",
                "starter_code": {
                    "java": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        String s = sc.nextLine().trim();\n        // TODO: check palindrome\n    }\n}\n",
                    "python": "s = input().strip()\nprint('YES' if s == s[::-1] else 'NO')\n",
                    "cpp": "#include <iostream>\n#include <string>\n#include <algorithm>\nusing namespace std;\n\nint main() {\n    string s;\n    cin >> s;\n    string r = s;\n    reverse(r.begin(), r.end());\n    cout << (s == r ? \"YES\" : \"NO\") << endl;\n    return 0;\n}\n"
                },
                "test_cases": [
                    {"input": "racecar", "output": "YES", "hidden": False, "marks": 5},
                    {"input": "skillbyte", "output": "NO", "hidden": True, "marks": 5},
                    {"input": "madam", "output": "YES", "hidden": True, "marks": 5},
                ]
            },

            # C++ Coding Problem
            {
                "title": "Maximum of Three Numbers",
                "description": "Given three integers A, B, and C, output the maximum of the three numbers.",
                "category": Category.CPP,
                "difficulty": DifficultyLevel.EASY,
                "marks": 10,
                "time_limit": 2,
                "memory_limit": 128,
                "input_format": "Three space-separated integers A, B, C.",
                "output_format": "Print the maximum value.",
                "constraints": "-10^6 <= A, B, C <= 10^6",
                "sample_input": "12 45 30",
                "sample_output": "45",
                "starter_code": {
                    "cpp": "#include <iostream>\n#include <algorithm>\nusing namespace std;\n\nint main() {\n    int a, b, c;\n    cin >> a >> b >> c;\n    cout << max({a, b, c}) << endl;\n    return 0;\n}\n",
                    "python": "a, b, c = map(int, input().split())\nprint(max(a, b, c))\n",
                    "java": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt();\n        int b = sc.nextInt();\n        int c = sc.nextInt();\n        System.out.println(Math.max(a, Math.max(b, c)));\n    }\n}\n"
                },
                "test_cases": [
                    {"input": "12 45 30", "output": "45", "hidden": False, "marks": 4},
                    {"input": "-5 -20 -1", "output": "-1", "hidden": True, "marks": 3},
                    {"input": "100 100 50", "output": "100", "hidden": True, "marks": 3},
                ]
            },

            # DSA Problem
            {
                "title": "Array Element Frequency",
                "description": "Given N integers and a target query K, count how many times K appears in the array.",
                "category": Category.DSA,
                "difficulty": DifficultyLevel.MEDIUM,
                "marks": 20,
                "time_limit": 2,
                "memory_limit": 256,
                "input_format": "First line: N and K.\nSecond line: N space-separated integers.",
                "output_format": "Print the integer count of occurrences of K.",
                "constraints": "1 <= N <= 10^5, -10^9 <= K <= 10^9",
                "sample_input": "5 3\n1 3 5 3 2",
                "sample_output": "2",
                "starter_code": {
                    "python": "n, k = map(int, input().split())\narr = list(map(int, input().split()))\nprint(arr.count(k))\n",
                    "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    int n, k;\n    cin >> n >> k;\n    int count = 0;\n    for(int i = 0; i < n; i++) {\n        int val;\n        cin >> val;\n        if(val == k) count++;\n    }\n    cout << count << endl;\n    return 0;\n}\n",
                    "java": "import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        int k = sc.nextInt();\n        int count = 0;\n        for (int i = 0; i < n; i++) {\n            if (sc.nextInt() == k) count++;\n        }\n        System.out.println(count);\n    }\n}\n"
                },
                "test_cases": [
                    {"input": "5 3\n1 3 5 3 2", "output": "2", "hidden": False, "marks": 6},
                    {"input": "6 7\n1 2 3 4 5 6", "output": "0", "hidden": True, "marks": 7},
                    {"input": "4 9\n9 9 9 9", "output": "4", "hidden": True, "marks": 7},
                ]
            },
        ]

        coding_created = 0
        testcases_created = 0

        for item in coding_data:
            q, created = Question.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "question_type": QuestionType.CODE,
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "marks": item["marks"],
                    "time_limit": item["time_limit"],
                    "memory_limit": item["memory_limit"],
                    "input_format": item["input_format"],
                    "output_format": item["output_format"],
                    "constraints": item["constraints"],
                    "sample_input": item["sample_input"],
                    "sample_output": item["sample_output"],
                    "starter_code": item["starter_code"],
                    "is_active": True,
                }
            )
            if created:
                coding_created += 1
                for tc in item["test_cases"]:
                    TestCase.objects.create(
                        question=q,
                        input_data=tc["input"],
                        expected_output=tc["output"],
                        is_hidden=tc["hidden"],
                        marks=tc["marks"],
                        time_limit=item["time_limit"],
                        memory_limit=item["memory_limit"],
                    )
                    testcases_created += 1

        self.stdout.write(self.style.SUCCESS(f"Coding Problems: {coding_created} seeded with {testcases_created} test cases."))
        self.stdout.write(self.style.SUCCESS("=== Question bank seeding complete ==="))

