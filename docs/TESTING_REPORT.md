# SKILLBYTE — Quality Assurance & Testing Report

> **Document ID**: `DELIV-04`  
> **Classification**: Quality Assurance & Verification Report  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Automated Suite Verdict**: **68 / 68 PASS (100%)**  
> **CDP Browser Verdict**: **10 / 10 PASS (0 Console Errors)**  
> **Database Integrity**: **PASS (0 Anomalies)**  

---

## 1. Testing Philosophy & Verification Strategy

SkillByte was verified following a rigorous multi-layered testing pyramid designed to ensure mathematical correctness, system resilience, and a pristine user experience.

```
                  / \
                 /   \
                / CDP \        End-to-End Headless Browser Tests
               / Browser\      (10 Scenarios, 0 Console Errors)
              /-----------\
             / Integration \    REST API & Database Rollback Tests
            /  API Testing  \   (68 Automated Test Cases)
           /-----------------\
          /   Model & Service \  Unit Tests: Scoring Deduplication,
         /      Unit Tests     \ Hashing, Sanitization, Limits
        /-----------------------\
```

### 1.1 Core Testing Principles
1. **Transactional Isolation**: All automated tests run within isolated PostgreSQL transaction wrappers that roll back state after each test method, preventing test pollution.
2. **Zero Client Trust**: Verification ensures that no business logic (timer calculations, hidden grading, answer checking) relies on client assertions.
3. **Dual Execution Verification**: Testing encompasses both simulated API requests (`rest_framework.test.APITestCase`) and real browser execution using Chrome DevTools Protocol (CDP) to validate DOM dynamics, Monaco editor bindings, and clipboard interactions.

---

## 2. Automated Test Suite Execution Summary (68 / 68 PASS)

### 2.1 Official Test Execution Log
```shell
$ python manage.py test questions.tests_phase11 questions.tests_phase10 questions.tests_phase9 questions.tests accounts
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....................................................................
----------------------------------------------------------------------
Ran 68 tests in 75.260s

OK
Destroying test database for alias 'default'...
```

---

### 2.2 Test Suite Breakdown by Functional Area

| Suite ID | Test Module | Test Count | Target Scope | Verdict |
|---|---|:---:|---|:---:|
| **TS-01** | `questions.tests_phase11` | **12** | Profile update, password change, assessment resumption, abandonment, CSV export RBAC, 404/403 handlers, throttling | **PASS** |
| **TS-02** | `questions.tests_phase10` | **11** | Unified scoring deduplication, skill tiers, leaderboard timeframe/category filtering, admin analytics KPIs, Run Code execution | **PASS** |
| **TS-03** | `questions.tests_phase9` | **15** | Admin Question Bank CRUD, MCQ creation with option validation, Coding problem with test cases, toggle active status, soft/hard deletion, RBAC enforcement | **PASS** |
| **TS-04** | `questions.tests` | **16** | Question listing, category/difficulty filtering, MCQ assessment start/submit, coding assessment start/submit, scoring calculations | **PASS** |
| **TS-05** | `accounts.tests` | **14** | Registration, login with email and username, JWT token rotation and blacklisting, role-based access control, guest session tracking | **PASS** |
| **TOTAL** | **5 Test Suites** | **68** | **Comprehensive Full-Platform Coverage** | **100% PASS** |

---

### 2.3 Detailed Method-Level Test Case Inventory

#### Suite 1: `questions.tests_phase11` (12 Tests)
1. `test_get_current_user_profile`: Validates that `GET /api/auth/me/` returns the authenticated student's profile, bio, role, and email.
2. `test_update_user_profile`: Validates that `PATCH /api/auth/me/` updates first name, last name, and bio, and reflects immediately.
3. `test_change_password_success`: Validates password update with valid old password, matching new passwords, and PBKDF2 re-hashing.
4. `test_change_password_invalid_old_password`: Ensures HTTP 400 rejection when the existing password is incorrect.
5. `test_active_assessment_detection`: Validates that `GET /api/assessments/active/` identifies in-progress MCQ or coding attempts.
6. `test_active_assessment_none_when_completed`: Validates that completed attempts are not flagged as active.
7. `test_abandon_in_progress_assessment`: Validates that `POST /api/assessments/<id>/abandon/` transitions attempt status to `ABANDONED` and awards 0 points.
8. `test_abandon_forbidden_for_other_user`: Ensures students cannot abandon attempts owned by other candidates (HTTP 403 / 404).
9. `test_admin_analytics_export_csv_authorized`: Validates that an authenticated administrator receives `Content-Type: text/csv` with valid rows.
10. `test_admin_analytics_export_csv_forbidden_for_student`: Validates that students and guests receive HTTP 403 when requesting the CSV export.
11. `test_custom_404_handler`: Validates that undefined routes render the custom branded SkillByte 404 template with status code 404.
12. `test_custom_403_handler`: Validates that forbidden requests render the custom branded 403 template with status code 403.

#### Suite 2: `questions.tests_phase10` (11 Tests)
13. `test_unified_scoring_best_score_deduplication`: Validates that submitting the same question multiple times takes `MAX(score)` rather than summing points.
14. `test_skill_tier_assignment`: Validates threshold classification: Novice (0–49), Apprentice (50–149), Specialist (150–299), Master (300+).
15. `test_leaderboard_all_time_ranking`: Validates ranking order sorted descending by deduplicated points.
16. `test_leaderboard_category_filtering`: Validates that filtering by category (e.g., Python) considers only questions in that subject.
17. `test_leaderboard_timeframe_filtering`: Validates 7-day and 30-day window filtering against `submitted_at`.
18. `test_admin_analytics_kpis`: Validates KPI computation: Total Users, Total Attempts, Completion Rate, and Average Scores.
19. `test_admin_analytics_category_breakdown`: Validates attempt distribution across subjects.
20. `test_run_code_sample_test_cases`: Validates execution against public test cases (`is_hidden=False`) returning stdout and status.
21. `test_run_code_does_not_mutate_attempt_score`: Ensures `/run/` does not finalize the assessment or award marks.
22. `test_run_code_syntax_error_verdict`: Validates that compilation errors return descriptive error messages without server 500s.
23. `test_run_code_rate_limiting`: Validates DRF throttling after exceeding the 30 req/min threshold.

#### Suite 3: `questions.tests_phase9` (15 Tests)
24. `test_admin_question_list_accessible_by_admin`: Verifies admin can view all questions (active and inactive).
25. `test_admin_question_list_forbidden_for_student`: Verifies students receive HTTP 403 on `/api/questions/admin/`.
26. `test_admin_create_mcq_success`: Validates MCQ creation with 4 options and a single marked correct answer.
27. `test_admin_create_mcq_missing_correct_option`: Validates rejection when no option is marked `is_correct=True`.
28. `test_admin_create_coding_question_success`: Validates coding problem creation with input/output format and starter code.
29. `test_admin_update_mcq`: Validates updating question text, marks, and option text.
30. `test_admin_update_coding_question`: Validates updating starter code templates and memory limits.
31. `test_admin_toggle_active_status`: Validates toggling `is_active` from True to False and vice versa.
32. `test_admin_soft_delete_question`: Validates archiving behavior.
33. `test_admin_create_test_case_public`: Validates adding a sample test case (`is_hidden=False`).
34. `test_admin_create_test_case_hidden`: Validates adding a hidden grading test case (`is_hidden=True`).
35. `test_admin_update_test_case`: Validates modifying expected output and weight.
36. `test_admin_delete_test_case`: Validates test case removal.
37. `test_admin_cannot_assign_mcq_category_to_code`: Validates model clean validation for category mismatches.
38. `test_admin_unauthenticated_blocked`: Validates HTTP 401 for unauthenticated calls to admin APIs.

#### Suite 4: `questions.tests` (16 Tests)
39. `test_public_question_list`: Validates public listing returns only active questions.
40. `test_public_question_detail_sanitized`: Validates `is_correct` stripped from MCQ options.
41. `test_mcq_start_assessment`: Validates attempt creation and question assignment.
42. `test_mcq_record_answer`: Validates recording option selection in `MCQAnswer`.
43. `test_mcq_submit_assessment`: Validates calculation of marks and creation of `AssessmentResult`.
44. `test_mcq_submit_time_expired`: Validates zero marks awarded when submission occurs past the deadline.
45. `test_coding_start_assessment`: Validates coding session initialization and time limit allocation.
46. `test_coding_detail_hidden_tests_omitted`: Validates that hidden test cases are never returned.
47. `test_coding_submit_all_passed`: Validates `ACCEPTED` verdict and full marks awarded.
48. `test_coding_submit_partial_credit`: Validates `PARTIAL` verdict and proportional scoring.
49. `test_coding_submit_wrong_answer`: Validates `WRONG_ANSWER` verdict when output mismatches.
50. `test_coding_submit_compilation_error`: Validates `COMPILATION_ERROR` handling.
51. `test_coding_submit_runtime_error`: Validates `RUNTIME_ERROR` handling.
52. `test_coding_submit_time_limit_exceeded`: Validates `TIME_LIMIT_EXCEEDED` handling.
53. `test_my_attempts_history_authenticated`: Validates that students see only their own sessions.
54. `test_my_attempts_history_guest`: Validates guest session tracking via `session_id`.

#### Suite 5: `accounts.tests` (14 Tests)
55. `test_user_registration_success`: Validates student creation and default `Role.STUDENT` assignment.
56. `test_user_registration_duplicate_username`: Validates rejection of existing usernames.
57. `test_user_registration_duplicate_email`: Validates rejection of existing emails.
58. `test_user_registration_password_mismatch`: Validates password confirmation check.
59. `test_login_with_username`: Validates JWT token pair generation on username authentication.
60. `test_login_with_email`: Validates JWT token pair generation on email authentication.
61. `test_login_invalid_credentials`: Validates HTTP 401 on incorrect password.
62. `test_token_refresh`: Validates new access token generation from refresh token.
63. `test_token_rotation_and_blacklisting`: Validates old refresh token cannot be reused after refresh.
64. `test_logout_blacklists_token`: Validates refresh token blacklisting on logout.
65. `test_student_role_permission`: Validates student access to student endpoints.
66. `test_admin_role_permission`: Validates admin access to admin endpoints.
67. `test_student_blocked_from_admin_endpoints`: Validates student access denial to admin endpoints.
68. `test_guest_session_generation`: Validates generation of guest session UUIDs.

---

## 3. Chrome / CDP End-to-End Browser Verification Matrix (10 / 10 PASS)

Browser verification was executed against the running local server (`http://127.0.0.1:8000`) using Chrome headless automation via Chrome DevTools Protocol (CDP).

| # | Scenario Description | Tested Route | Evaluated Conditions | Result | Console Errors |
|:---:|---|---|---|:---:|:---:|
| **1** | Student Profile Editing & Navbar Reflection | `/profile/` | Update bio & name; verify immediate DOM update in navbar and profile card | **PASS** | 0 |
| **2** | Secure Password Change | `/profile/` | Submit old/new password; verify success notification toast and re-login requirement | **PASS** | 0 |
| **3** | Responsive Navbar & Mobile Collapse | `/` | Resize viewport to 375px (iPhone); toggle hamburger menu; verify links accessible | **PASS** | 0 |
| **4** | Assessment Resumption | `/coding/assessment/<id>/` | Start attempt, trigger page reload; verify question, timer, and starter code restored | **PASS** | 0 |
| **5** | Assessment Abandonment | `/assessments/mcq/<id>/` | Click abandon button; confirm modal dialog; verify status transition to `ABANDONED` | **PASS** | 0 |
| **6** | Solution Utilities (Copy / Download / Practice Again) | `/coding/result/<id>/` | Test Copy Solution (clipboard toast); Download Code (`.py` blob); Practice Again CTA | **PASS** | 0 |
| **7** | Admin Analytics Dashboard & CSV Export | `/admin/analytics/` | Load KPIs & charts; click "Export CSV"; verify file download trigger & MIME type | **PASS** | 0 |
| **8** | RBAC Enforcement & Redirection | `/admin/questions/` | Navigate with Student/Guest credentials; verify HTTP 403 or redirect to login | **PASS** | 0 |
| **9** | Custom Branded Error Pages (404 / 403 / 500) | `/invalid-route-xyz/` | Visit unmapped URL; verify custom SkillByte branded 404 UI renders without Django debug stack | **PASS** | 0 |
| **10** | Console Error Monitoring | All Primary Views | Listen for `console.error` and `Page.javascriptDialogOpening` across all pages | **PASS** | **0** |

---

## 4. Edge Case & Fault Tolerance Verification

| Failure Mode | Injected Scenario | System Defense & Observed Behavior | Status |
|---|---|---|:---:|
| **Timer Expiration** | Candidate holds submission until $T > \text{time\_limit}$ | Server verifies timestamps; marks attempt as expired with 0 marks; locks attempt | **VERIFIED** |
| **Infinite Loop in Code** | Candidate submits `while True: pass` in Python | Judge0 enforces 2.0s CPU time limit; returns `TIME_LIMIT_EXCEEDED`; server reports TLE badge | **VERIFIED** |
| **Memory Bomb** | Candidate submits code allocating 10GB array | Judge0 cgroups kill process upon exceeding 256MB; returns `RUNTIME_ERROR` (Memory Limit) | **VERIFIED** |
| **Host System Call** | Candidate submits `import os; os.system('rm -rf /')` | Execution occurs inside non-root Docker container (`nobody`); command fails safely; host untouched | **VERIFIED** |
| **Sandbox Network Outage** | Judge0 container stopped during execution | Django catches connection timeout; returns `SERVICE_UNAVAILABLE` verdict with user-friendly retry message | **VERIFIED** |
| **Concurrent Submissions** | Double-clicking "Submit" within 50ms | Database row locking (`SELECT FOR UPDATE`) rejects second submission; only one is processed | **VERIFIED** |

