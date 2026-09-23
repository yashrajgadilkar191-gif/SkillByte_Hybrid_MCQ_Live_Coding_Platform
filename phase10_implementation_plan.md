# SKILLBYTE — Phase 10 Detailed Implementation Plan

> **Project**: SkillByte — *"Where Theory Meets Practice"*  
> **Phase**: Phase 10 — Leaderboard, Unified Scoring, Admin Analytics & Live Run Code  
> **Source of Truth**: SkillByte System Requirements Specification (SRS) & Architecture Documents  
> **Date**: September 23, 2026  
> **Author**: Lead Full-Stack Developer  
> **Status**: **Approved Revisions Awaiting Final Go-Ahead (No application code modified)**

---

## A. Phase 10 Objective

The objective of Phase 10 is to complete the final set of core functional requirements outlined in the original SkillByte SRS:
1. Deliver a public, category-wise and overall **Leaderboard** for registered students using a non-duplicative **Best Score per Unique Question** model.
2. Formulate and display an authoritative **Unified Score & Category Mastery** progress engine synthesizing theoretical MCQ marks and practical coding scores using the same unique-question deduplication standard.
3. Provide an executive-level **Admin Platform & Assessment Analytics** dashboard.
4. Upgrade the Monaco Editor workspace with a live **"Run Code"** pre-test execution feature running exclusively against public sample test cases via Judge0.
5. Preserve 100% of the verified functionality from Phases 1–9 without regressions.

---

## B. Detailed Scope for Modules 10A–10D

### MODULE 10A — Category-Wise & Overall Leaderboard
- **Backend API (`GET /api/leaderboard/`)**:
  - Computes student rankings across **Overall Platform** and individual **Categories** (`General Knowledge`, `English`, `Mathematics`, `Python`, `Java`, `C++`, `DSA`).
  - Supports query parameters: `category` (default `all`), `timeframe` (`all_time`, `month`, `week`), `limit` (default 50).
  - Implements **Best Score per Unique Question**: for any student in the selected scope, group attempts by unique question, take the highest `obtained_marks` achieved for each question, and sum them.
  - Returns ranking position (1, 2, 3...), student username, full name, total unified points, completed assessments count, average accuracy %, theory score, and coding score.
  - **Public Access Rules**:
    - **Guests**: Can freely view rankings; receive `current_user_rank: null`; never appear in ranking tables.
    - **Students**: Can view rankings; appear in rankings according to points; receive `current_user_rank` with personal standing.
    - **Admins**: Excluded from student rankings; viewing the leaderboard never alters rankings or student calculations.
- **Student-Facing Leaderboard Page (`/leaderboard/`)**:
  - Follows SkillByte glassmorphism dark navy theme (`bg-glass`, `text-light`).
  - Interactive top-3 **Podium Cards** (Gold #1, Silver #2, Bronze #3 with distinct gradient highlights).
  - Interactive category pills for instant filtering without full page reloads.
  - Timeframe selector buttons (All-Time, This Month, This Week).
  - Search input to locate a specific candidate or classmate.
  - Prominent "Your Standing" card displaying the logged-in student's current rank, points, and distance to the next rank (hidden for unauthenticated guests).
  - Navbar and Dashboard navigation integration.

---

### MODULE 10B — Unified Scoring & Student Progress
- **Unified Score Synthesis (Best Score per Unique Question)**:
  - For all completed assessments within the evaluation scope:
    - Group completed attempts by unique `Question`.
    - For each unique question, take the maximum `obtained_marks` recorded by that student.
    - Compute:
      $$\text{Unified Score} = \sum_{q \in \text{Unique Questions Attempted}} \max(\text{obtained\_marks}(q))$$
      $$\text{Theory Points} = \sum_{q \in \text{Unique MCQ Questions Attempted}} \max(\text{obtained\_marks}(q))$$
      $$\text{Coding Points} = \sum_{q \in \text{Unique Coding Problems Attempted}} \max(\text{obtained\_marks}(q))$$
  - **Unified Skill Rank Tiers**:
    - `0 - 49 pts`: **Novice** (Bronze badge)
    - `50 - 149 pts`: **Apprentice** (Silver badge)
    - `150 - 299 pts`: **Specialist** (Gold badge)
    - `300+ pts`: **Master** (Platinum badge)
- **Category Mastery Progress (Best Score per Unique Question)**:
  - Computes percentage proficiency per category without summing repeated attempts:
    $$\text{Category Mastery \%} = \frac{\sum_{q \in \text{Unique Questions Attempted in Category}} \max(\text{obtained\_marks}(q))}{\sum_{q \in \text{Unique Questions Attempted in Category}} q.\text{marks}} \times 100$$
  - Status classification:
    - `< 50%`: **Needs Practice**
    - `50% – 79%`: **Proficient**
    - `80%+`: **Mastered**
- **Enhanced Progress API (`GET /api/assessments/progress/`)**:
  - Extends existing Phase 8 endpoint with `unified_score`, `theory_score`, `coding_score`, `skill_tier`, `category_mastery` list, and `performance_timeline`.
  - Zero breaking changes to existing keys consumed by Phase 8 attempt history.
- **Dashboard UI Enhancements (`/dashboard/`)**:
  - Add Unified Skill Badge and total points counter to user header.
  - Add Category Mastery progress bars with gradient color scales.

---

### MODULE 10C — Admin Platform & Assessment Analytics
- **Admin-Only Analytics API (`GET /api/admin/analytics/`)**:
  - Strictly protected by `accounts.permissions.IsAdmin` (returns HTTP 403 for students, 401 for guests).
  - Computes platform-wide diagnostic aggregations:
    1. **Student Demographics**: Total registered students, active students (past 30 days), new signups.
    2. **Assessment Volume**: Total attempts, completed count, completion rate %, MCQ vs Coding ratio.
    3. **Category Performance**: Average percentage score, attempts volume, and pass rate (>=60%) for each category.
    4. **Coding Submission Verdict Breakdown**: Distribution of submission statuses: Accepted, Partial, Wrong Answer, Compilation Error, Runtime Error, Time Limit Exceeded.
    5. **Question Difficulty Diagnostics**: Top 5 hardest questions by lowest average score or highest error rate to identify problematic questions.
- **Admin Analytics Dashboard (`/admin/analytics/`)**:
  - Summary KPI metric cards.
  - Category pass rate meters and submission verdict distribution charts (styled with clean CSS/SVG components, avoiding heavy external JavaScript library dependencies).
  - Direct navigation link in the Admin Navbar and Question Bank header.

---

### MODULE 10D — Live "Run Code" in Monaco Workspace
- **Public Test Execution Endpoint (`POST /api/assessments/coding/<attempt_id>/run/`)**:
  - Validates attempt ownership and ensures attempt is `IN_PROGRESS` and `question_type == 'CODE'`.
  - Executes candidate's Monaco editor code against **ONLY Sample / Public Test Cases** (`question.test_cases.filter(is_hidden=False)`).
  - **Zero Leakage**: Hidden test cases (`is_hidden=True`) are completely excluded from the query.
  - Uses existing `Judge0Service.execute_test_case()`.
  - Does NOT close or complete the `AssessmentAttempt`; does NOT create an `AssessmentResult`.
  - Returns detailed test run feedback: `{ status, execution_time, memory_usage, test_cases_passed, total_sample_cases, sample_results: [{ case_number, input, expected_output, actual_output, passed, status_description, stderr, compile_output }] }`.
- **Monaco Workspace UI Integration (`coding_assessment.html`)**:
  - Replace the current informational "Run Code" modal with live asynchronous execution.
  - Show spinner `"Executing against sample test cases via Judge0..."`.
  - Display test case tabs (Case 1, Case 2...) with pass/fail indicators, input, expected output, and candidate output.
  - "Submit Solution" remains authoritative for final submission and evaluation of all sample and hidden test cases.

---

## C. Existing Files, Models, and Services to Reuse

| Component | File Path | What Will Be Reused |
| :--- | :--- | :--- |
| **Question Models** | [`backend/questions/models.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/models.py) | `Question`, `QuestionOption`, `TestCase`, `Category`, `QuestionType`, `DifficultyLevel`. |
| **Attempt & Result Models** | [`backend/questions/models.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/models.py) | `AssessmentAttempt`, `AssessmentResult`, `CodingSubmission`, `MCQAnswer`, `SubmissionStatus`, `AttemptStatus`. |
| **RBAC Permissions** | [`backend/accounts/permissions.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/permissions.py) | `IsAdmin`, `IsStudent`, `IsGuestOrReadOnly`. |
| **Judge0 Service** | [`backend/questions/judge0_service.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/judge0_service.py) | `Judge0Service.execute_test_case()`, `LANGUAGE_IDS`. |
| **Attempt Access Helper** | [`backend/questions/assessment_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_views.py) | `get_attempt_for_request(attempt_id, request)`. |
| **Client Auth Manager** | [`frontend/static/js/auth.js`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/static/js/auth.js) | `Auth.fetchWithAuth()`, token refresh, navbar rendering. |
| **Templates** | `frontend/templates/base.html`, `dashboard.html` | Base layout, navbar slots, existing progress card markup. |

---

## D. New Files and Views to Create

1. **Backend Views & Services**:
   - `backend/questions/leaderboard_views.py`: `LeaderboardView` (`GET /api/leaderboard/`).
   - `backend/questions/analytics_views.py`: `AdminAnalyticsView` (`GET /api/admin/analytics/`).
   - In `backend/questions/assessment_views.py`: Add `CodingAssessmentRunCodeView` (`POST /api/assessments/coding/<attempt_id>/run/`).
2. **Frontend Templates**:
   - `frontend/templates/leaderboard.html`: Modern glassmorphism Leaderboard page with podium, category pills, and personal rank banner.
   - `frontend/templates/admin/analytics.html`: Admin Platform Analytics dashboard.
3. **Automated Test Suite**:
   - `backend/questions/tests_phase10.py`: Unit and integration test suite covering Leaderboard, Unique Question Deduplication, Category Mastery, Admin Analytics, and Run Code.

---

## E. API Endpoint Design

### 1. Leaderboard API
- **Endpoint**: `GET /api/leaderboard/`
- **Access**: `AllowAny` (Public read-only).
- **Query Parameters**:
  - `category` (optional, string, e.g. `Python`, `Mathematics`, default: `all`)
  - `timeframe` (optional: `all_time`, `month`, `week`, default: `all_time`)
  - `limit` (optional, int, default: 50)
- **Response Format (`HTTP 200 OK`)**:
  ```json
  {
    "category": "All Categories",
    "timeframe": "all_time",
    "total_ranked_students": 42,
    "current_user_rank": {
      "rank": 3,
      "user_id": 15,
      "username": "alex_student",
      "name": "Alex Mercer",
      "total_score": 185.0,
      "accuracy_percentage": 92.5,
      "unique_questions_completed": 8
    },
    "rankings": [
      {
        "rank": 1,
        "user_id": 8,
        "username": "coder_pro",
        "name": "Devin Smith",
        "total_score": 240.0,
        "theory_score": 60.0,
        "coding_score": 180.0,
        "unique_questions_completed": 12,
        "accuracy_percentage": 96.0,
        "skill_tier": "Specialist"
      }
    ]
  }
  ```
  *(Note: If request is unauthenticated or from a guest, `current_user_rank` is returned as `null`.)*

### 2. Enhanced Student Progress API
- **Endpoint**: `GET /api/assessments/progress/`
- **Access**: `AllowAny` (Student or Guest via `session_id`).
- **Additional Response Keys (Non-breaking additive changes)**:
  ```json
  {
    "total_attempts": 10,
    "completed_attempts": 8,
    "in_progress_attempts": 2,
    "mcq_count": 6,
    "coding_count": 4,
    "average_percentage": 88.5,
    "average_score": 22.1,
    "unified_score": 185.0,
    "theory_score": 45.0,
    "coding_score": 140.0,
    "skill_tier": "Specialist",
    "skill_badge_class": "badge-specialist",
    "category_mastery": [
      { "category": "Python", "type": "CODE", "mastery_percentage": 95.0, "status": "Mastered", "unique_questions": 3 },
      { "category": "Mathematics", "type": "MCQ", "mastery_percentage": 78.0, "status": "Proficient", "unique_questions": 2 }
    ]
  }
  ```

### 3. Admin Analytics API
- **Endpoint**: `GET /api/admin/analytics/`
- **Access**: `IsAdmin` only (HTTP 401 for unauthenticated, HTTP 403 for students).
- **Response Format (`HTTP 200 OK`)**:
  ```json
  {
    "students": {
      "total_registered": 120,
      "active_30d": 84,
      "new_30d": 18
    },
    "assessments": {
      "total_attempts": 350,
      "completed_attempts": 298,
      "completion_rate": 85.1,
      "mcq_attempts": 210,
      "coding_attempts": 140
    },
    "category_performance": [
      { "category": "Python", "attempts": 80, "avg_percentage": 82.4, "pass_rate": 88.0 },
      { "category": "Mathematics", "attempts": 75, "avg_percentage": 71.0, "pass_rate": 74.5 }
    ],
    "coding_verdicts": {
      "ACCEPTED": 120,
      "PARTIAL": 35,
      "WRONG_ANSWER": 42,
      "COMPILATION_ERROR": 12,
      "RUNTIME_ERROR": 8,
      "TIME_LIMIT_EXCEEDED": 5
    },
    "hardest_questions": [
      { "id": 4, "title": "Reverse Linked List", "type": "CODE", "category": "Python", "avg_percentage": 42.0, "attempts_count": 25 }
    ]
  }
  ```

### 4. Live Run Code API
- **Endpoint**: `POST /api/assessments/coding/<attempt_id>/run/`
- **Access**: Attempt Owner only (`get_attempt_for_request`).
- **Request Body**:
  ```json
  {
    "source_code": "def solution(nums):\n    return nums[::-1]\n",
    "language": "python"
  }
  ```
- **Response Format (`HTTP 200 OK`)**:
  ```json
  {
    "status": "ACCEPTED",
    "execution_time": 0.042,
    "memory_usage": 7420,
    "sample_cases_passed": 2,
    "total_sample_cases": 2,
    "results": [
      {
        "case_number": 1,
        "input_data": "[1, 2, 3]",
        "expected_output": "[3, 2, 1]",
        "actual_output": "[3, 2, 1]\n",
        "passed": true,
        "status_description": "Accepted",
        "stderr": "",
        "compile_output": ""
      }
    ]
  }
  ```

---

## F. Database Changes

### Decision: Pure Dynamic Aggregation over PostgreSQL
- **Approach**: Dynamic aggregation using Django ORM (`Max`, `Sum`, `Count`, `Avg`, `Q`) over existing `AssessmentAttempt`, `AssessmentResult`, `MCQAnswer`, `CodingSubmission`, and `UserProfile` tables.
- **Rationale**:
  1. Prevents duplicate data, eliminates synchronization lag, and ensures immediate leaderboard updates upon submission.
  2. The unique question deduplication logic is executed via database queries (`values('user', 'question').annotate(best_score=Max('score'))`).
  3. **Zero Schema Migrations Required**: All underlying models already contain the required foreign keys and indexing.

---

## G. Unified Scoring Formula (Best Score per Unique Question)

1. **Attempt Score Ground Truth**:
   - For MCQ: $\text{Attempt Score} = \sum_{\text{correct}} \text{question.marks}$
   - For Code: $\text{Attempt Score} = \text{question.marks} \times \left(\frac{\text{passed\_test\_cases}}{\text{total\_test\_cases}}\right)$
   - Recorded authoritatively in `AssessmentResult.obtained_marks`.
2. **Student Cumulative Points Deduplication**:
   - For Coding: An attempt tests 1 question. Best score for question $Q$ is $\max(\text{obtained\_marks})$ across all completed attempts for question $Q$.
   - For MCQ: An attempt has $N$ questions. Individual question marks are stored in `MCQAnswer.marks_obtained`. Best score for question $Q$ is $\max(\text{marks\_obtained})$ across all completed attempts containing question $Q$.
   - **Unified Score Formula**:
     $$\text{Unified Score} = \sum_{q \in \text{Unique Questions Attempted}} \text{Best Marks}(q)$$
     $$\text{Theory Score} = \sum_{q \in \text{Unique MCQ Questions Attempted}} \text{Best Marks}(q)$$
     $$\text{Coding Score} = \sum_{q \in \text{Unique Coding Problems Attempted}} \text{Best Marks}(q)$$
   - *Repeated attempts for the same question never add duplicate points.*

3. **Category Mastery Formula (Best Score per Unique Question)**:
   $$\text{Category Mastery \%} = \frac{\sum_{q \in \text{Unique Questions Attempted in Category}} \text{Best Marks}(q)}{\sum_{q \in \text{Unique Questions Attempted in Category}} q.\text{marks}} \times 100$$
   - Classification:
     - `< 50%`: **Needs Practice**
     - `50% – 79%`: **Proficient**
     - `80%+`: **Mastered**

---

## H. Leaderboard Calculation & Timeframe Logic

### Timeframe Scoping
1. **All-Time**:
   - Query all completed attempts: `AssessmentAttempt.objects.filter(status=AttemptStatus.COMPLETED, user__isnull=False, user__profile__role=Role.STUDENT, user__is_staff=False, user__is_superuser=False)`.
2. **This Month**:
   - Filter attempts first to those submitted in the current month / last 30 days: `submitted_at >= timezone.now() - timedelta(days=30)`.
   - Then apply best score per unique question deduplication on the filtered set.
3. **This Week**:
   - Filter attempts first to those submitted in the current week / last 7 days: `submitted_at >= timezone.now() - timedelta(days=7)`.
   - Then apply best score per unique question deduplication on the filtered set.

### Category Scoping
- If `category` is specified (e.g. `Python`), filter attempts to `category__iexact=category`.

### Ranking Algorithm
1. Compute student aggregated metrics:
   - `total_score` = sum of best marks per unique question in scope.
   - `unique_questions_completed` = count of distinct questions evaluated in scope.
   - `accuracy_percentage` = $(\text{total\_score} / \text{total\_possible\_marks\_for\_those\_questions}) \times 100$.
   - `theory_score` = sum of best marks for MCQ questions.
   - `coding_score` = sum of best marks for Coding problems.
2. Sort candidates by:
   1. `-total_score` (highest points first)
   2. `-accuracy_percentage` (tie-breaker: higher accuracy)
   3. `-unique_questions_completed` (tie-breaker: more questions solved)
   4. `user__username` (deterministic final tie-breaker)
3. Assign sequential positions: `rank = 1, 2, 3...`
4. If requester is an authenticated student, locate their position and return `current_user_rank`. If unauthenticated or guest, set `current_user_rank = null`.

---

## I. Analytics Calculation Logic

1. **Student Demographics**:
   - `total_registered = UserProfile.objects.filter(role=Role.STUDENT).count()`
   - `active_30d = AssessmentAttempt.objects.filter(started_at__gte=thirty_days_ago, user__isnull=False).values('user').distinct().count()`
   - `new_30d = User.objects.filter(date_joined__gte=thirty_days_ago, profile__role=Role.STUDENT).count()`
2. **Assessment Volume & Conversion**:
   - `total = AssessmentAttempt.objects.count()`
   - `completed = AssessmentAttempt.objects.filter(status=AttemptStatus.COMPLETED).count()`
   - `completion_rate = (completed / total * 100) if total > 0 else 0.0`
   - `mcq = AssessmentAttempt.objects.filter(question_type=QuestionType.MCQ).count()`
   - `coding = AssessmentAttempt.objects.filter(question_type=QuestionType.CODE).count()`
3. **Category Performance Diagnostics**:
   - For each Category:
     - Total completed attempts.
     - Average percentage on completed attempts.
     - Pass rate: percentage of completed attempts with score $\ge 60\%$.
4. **Coding Submission Verdict Breakdown**:
   - Count of `CodingSubmission` grouped by `status` (`ACCEPTED`, `PARTIAL`, `WRONG_ANSWER`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`).
5. **Question Diagnostic (Hardest Questions)**:
   - For each active question with $\ge 3$ attempts, compute average percentage achieved across all attempts.
   - Return top 5 lowest scoring questions to highlight challenging concepts to administrators.

---

## J. Run Code Execution Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Monaco as Monaco Editor (Browser)
    participant API as CodingAssessmentRunCodeView
    participant DB as PostgreSQL
    participant Judge0 as Judge0 Engine

    Student->>Monaco: Clicks "Run Code"
    Monaco->>API: POST /api/assessments/coding/<id>/run/ {source_code, language}
    API->>API: Validate attempt ownership & status (IN_PROGRESS)
    API->>DB: Fetch Question & SAMPLE test cases only (is_hidden=False)
    Note over API,DB: Hidden test cases strictly excluded!
    loop For each sample test case
        API->>Judge0: Judge0Service.execute_test_case(source_code, lang, sample_case)
        Judge0-->>API: stdout, stderr, status, execution_time, memory
    end
    API->>Monaco: Return sample test results & diffs (HTTP 200)
    Note over API,DB: Attempt remains IN_PROGRESS; AssessmentResult is NOT created
    Monaco-->>Student: Renders execution console (Passed/Failed per sample case)
```

---

## K. Security Considerations

1. **Public Leaderboard Security**:
   - Guest identifiers and temporary session IDs are strictly omitted from ranking queries.
   - Admin accounts (`role == Role.ADMIN`, `is_staff`, `is_superuser`) are strictly excluded from ranking calculations.
   - Passwords, email addresses, and JWT tokens are never serialized in leaderboard payloads (only public username, display name, points, and badge are exposed).
2. **Hidden Test Case Protection**:
   - `CodingAssessmentRunCodeView` queries **only** `question.test_cases.filter(is_hidden=False)`.
   - Hidden test cases are never evaluated or referenced during "Run Code", preventing any candidate from extracting hidden inputs or outputs via trial-and-error stdout.
3. **No Arbitrary Local Code Execution**:
   - All code execution flows exclusively through the remote sandboxed Judge0 Docker API.
4. **Authoritative Timers & Assessment State**:
   - "Run Code" does not extend or reset the assessment attempt timer.
   - "Run Code" cannot be invoked on `COMPLETED` or expired attempts.
5. **Admin Analytics Access Guard**:
   - Strict `accounts.permissions.IsAdmin` enforcement (HTTP 403 for students, 401 for guests).

---

## L. Test Strategy

We will write `backend/questions/tests_phase10.py` verifying:
1. **Leaderboard**:
   - Ranked order (highest points first, tie-breaking by accuracy).
   - Category filtering (e.g. `?category=Python`).
   - Deduplication: Verifying that re-taking the same question with the same or lower score does NOT increase leaderboard points.
   - Exclusion of guest attempts and admin profiles.
   - Public view: Unauthenticated client receives HTTP 200 with `current_user_rank: null`.
   - Authenticated student receives HTTP 200 with accurate `current_user_rank`.
2. **Unified Scoring & Category Mastery**:
   - Correct aggregation of Theory and Coding points.
   - Best score per unique question deduplication in Category Mastery percentage.
   - Skill tier assignment (*Novice* vs *Master*).
3. **Admin Analytics**:
   - Access control (Admin 200, Student 403, Guest 401).
   - Accuracy of student counts, completion rates, category stats, and verdict distribution.
4. **Live Run Code**:
   - Execution against sample cases only.
   - Verified that hidden test cases are not executed or leaked.
   - Verified that attempt status remains `IN_PROGRESS` and no `AssessmentResult` is created.

---

## M. Regression Testing Strategy

After Phase 10 implementation, the following test suites must all execute with zero errors:
```powershell
python manage.py check
python manage.py test questions.tests_phase10
python manage.py test questions.tests_phase9
python manage.py test questions.tests
python manage.py test accounts
```

---

## N. Chrome Browser & CDP Verification Checklist

1. **Leaderboard Page (`/leaderboard/`)**:
   - Load page as unauthenticated guest; verify top-3 podium renders, table renders, and personal rank banner is hidden.
   - Log in as student; verify personal rank card appears highlighting student's position.
   - Test category pills (General Knowledge, Mathematics, Python, C++, etc.); verify table updates seamlessly.
2. **Student Dashboard (`/dashboard/`)**:
   - Verify Unified Score widget and Category Mastery progress meters display properly.
3. **Admin Analytics Page (`/admin/analytics/`)**:
   - Log in as Admin; verify access to student metrics, assessment volume, category pass rates, and submission verdict distribution.
   - Access `/admin/analytics/` as Student; verify HTTP 403 access denial.
4. **Coding Workspace Run Code (`/coding/assessment/<attempt_id>/`)**:
   - Open Monaco workspace, enter solution, and click "Run Code".
   - Verify live execution against sample test cases and inspect console results.
   - Click "Submit Solution"; verify full evaluation runs through Judge0 and leads to results page.
5. **Console Integrity**:
   - Zero JavaScript console errors throughout all browser interactions.

---

## O. Implementation Order and Dependencies

```
[Module 10D: Run Code Endpoint & Monaco UI] 
         ↓
[Module 10B: Unified Scoring & Progress Engine]
         ↓
[Module 10A: Leaderboard API & UI]
         ↓
[Module 10C: Admin Analytics API & UI]
         ↓
[Automated Tests & Browser Verification]
```

---

## P. Definition of Done

- [x] Revisions incorporated into `phase10_implementation_plan.md`.
- [ ] User approval received to proceed with implementation.
- [ ] All 4 modules (10A, 10B, 10C, 10D) are fully implemented.
- [ ] `python manage.py check` passes with 0 issues.
- [ ] `questions.tests_phase10` passes with 100% success.
- [ ] Existing test suites (`questions.tests_phase9`, `questions.tests`, `accounts`) pass with 0 regressions.
- [ ] Chrome CDP automated browser verification passes with 0 console errors.
- [ ] No Phase 1–9 code or Judge0 evaluation behavior broken or rebuilt.
