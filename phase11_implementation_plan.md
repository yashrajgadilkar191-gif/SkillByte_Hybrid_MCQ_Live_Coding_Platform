# SKILLBYTE — Phase 11 Detailed Implementation Plan

> **Project**: SkillByte — *"Where Theory Meets Practice"*  
> **Phase**: Phase 11 — Student Profile Management, Assessment Resumption, Solution Utilities & Platform Hardening  
> **Source of Truth**: SkillByte System Requirements Specification (SRS) & `phase11_gap_analysis.md`  
> **Date**: September 23, 2026  
> **Author**: Lead Full-Stack Developer  
> **Status**: **Planning Stage — Awaiting User Approval (No Application Code Modified)**

---

## A. Phase 11 Executive Summary & Goals

Phases 1 through 10 have achieved 100% test pass rates across all 56 automated test cases, complete PostgreSQL integrity, and full browser CDP validation of the core hybrid assessment, Judge0 sandboxing, leaderboards, and analytics systems.

The objective of **Phase 11** is to resolve all remaining non-future SRS gaps identified in `phase11_gap_analysis.md`:
1. **Module 11A**: Student Profile Editing, Password Change API, Student Profile UI, and Navbar Harmonization.
2. **Module 11B**: Assessment Session Lifecycle Resumption, In-Progress Attempt Detection, and Clean Abandonment.
3. **Module 11C**: Coding Solution Review Utilities (Copy, Download `.py`/`.java`/`.cpp`, Practice Again CTA) and Admin Analytics CSV Export.
4. **Module 11D**: Platform Reliability & Security Hardening (Custom 404, 403, 500 error pages, and DRF rate-limiting on sensitive endpoints).

---

## B. Strict Architectural Constraints & Integrity Guarantees

1. **Preserve Phases 1–10**:
   - Zero modifications to the Judge0 execution engine (`Judge0Service`).
   - Zero modifications to the Phase 10 Best-Score-Per-Unique-Question deduplication scoring logic (`calculate_student_progress`, `LeaderboardView`).
   - Zero modifications to the Phase 9 Admin Question Bank management logic and delete protection.
2. **No Unnecessary Migrations**:
   - All required models (`User`, `UserProfile`, `AssessmentAttempt`, `AttemptStatus.ABANDONED`) already exist. No schema alterations or migrations are required.
3. **Zero Security Regressions**:
   - Hidden test cases (`is_hidden=True`) remain strictly sanitized from all student-facing endpoints.
   - Admin routes and analytics exports remain strictly protected by `accounts.permissions.IsAdmin`.
   - Rate limiting must protect endpoints without breaking automated unit tests.

---

## C. Module-by-Module Technical Implementation Specifications

---

### MODULE 11A — Student Profile & Account Security

#### 1. Objective
Allow authenticated students to inspect their account profile, update basic personal details (first name, last name, email), and securely change their account password with validation. Clean up navbar redundancies and add responsive mobile collapse.

#### 2. Existing Code / Files to Reuse
- `backend/accounts/models.py` (`User`, `UserProfile`, `Role`).
- `backend/accounts/views.py` (`CurrentUserView`).
- `backend/accounts/serializers.py` (`UserSerializer`).
- `frontend/static/js/auth.js` (`Auth.fetchWithAuth`, `Auth.updateNavUI`).
- `frontend/templates/base.html` (navbar container).

#### 3. Files to Create / Modify
- **[MODIFY]** [`backend/accounts/serializers.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/serializers.py):
  - Add `UserProfileUpdateSerializer` (fields: `first_name`, `last_name`, `email`; validates email uniqueness).
  - Add `ChangePasswordSerializer` (fields: `old_password`, `new_password`, `new_password_confirm`; verifies `check_password`, enforces Django's `validate_password`).
- **[MODIFY]** [`backend/accounts/views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/views.py):
  - Extend `CurrentUserView` with `PUT`/`PATCH` handling via `UserProfileUpdateSerializer`.
  - Add `ChangePasswordView` (`APIView`, `permission_classes = [IsAuthenticated]`).
- **[MODIFY]** [`backend/accounts/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/urls.py):
  - Register `path('change-password/', ChangePasswordView.as_view(), name='auth_change_password')`.
- **[NEW]** `frontend/templates/profile.html`:
  - Glassmorphism user profile card displaying name, email, username, role, date joined.
  - Unified Score badge, Theory score, Coding score, and Skill Tier display.
  - "Edit Profile" form (updates first name, last name, email).
  - "Change Password" form (old password, new password, confirm password) with error and success alerts.
- **[MODIFY]** [`backend/config/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/urls.py) and [`backend/api/views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/api/views.py):
  - Register `path('profile/', profile_page_view, name='profile_page')`.
- **[MODIFY]** [`frontend/static/js/auth.js`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/static/js/auth.js):
  - Fix bug: remove duplicate `${adminLink}` so "Question Bank" is only rendered once.
  - Add `<a href="/profile/" class="btn btn-outline-light btn-sm"><i class="bi bi-person-circle me-1"></i>Profile</a>` for authenticated students and admins.
- **[MODIFY]** [`frontend/templates/base.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/base.html):
  - Add responsive Bootstrap navbar toggler `<button class="navbar-toggler" ...>` and `<div class="collapse navbar-collapse" id="navbarNav">` for mobile screens.

#### 4. API Endpoints & Contracts

##### Endpoint A1: `PUT / PATCH /api/auth/me/`
- **Access**: Authenticated (`IsAuthenticated`)
- **Request Body**:
  ```json
  {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.updated@example.com"
  }
  ```
- **Validation Rules**:
  - `email`: Valid email format; must be unique across all users (excluding current user).
  - `first_name`, `last_name`: Max length 150 characters.
  - Strips leading/trailing whitespaces.
- **Response `200 OK`**:
  ```json
  {
    "id": 4,
    "username": "alice_phase10",
    "email": "alice.updated@example.com",
    "first_name": "Alice",
    "last_name": "Smith",
    "name": "Alice Smith",
    "role": "STUDENT"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: Email already in use or invalid email format.
  - `401 Unauthorized`: Missing or expired JWT.

##### Endpoint A2: `POST /api/auth/change-password/`
- **Access**: Authenticated (`IsAuthenticated`)
- **Request Body**:
  ```json
  {
    "old_password": "CurrentPassword123!",
    "new_password": "NewSecurePassword456!",
    "new_password_confirm": "NewSecurePassword456!"
  }
  ```
- **Validation Rules**:
  - `old_password` must match `request.user.check_password()`.
  - `new_password` must match `new_password_confirm`.
  - `new_password` must pass Django standard password validators (`validate_password`).
  - `new_password` cannot be identical to `old_password`.
- **Response `200 OK`**:
  ```json
  {
    "status": "success",
    "message": "Password has been successfully updated."
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: Password mismatch, incorrect current password, or fails complexity.
  - `401 Unauthorized`: Unauthenticated.

#### 5. Database Changes
- **None**. Existing Django `auth_user` model fields are utilized directly.

#### 6. Security & RBAC
- Passwords are never returned in responses.
- Only the authenticated user can modify their own profile or password (`request.user`).
- Role cannot be changed via `/api/auth/me/` (`role` remains read-only).

---

### MODULE 11B — Assessment Lifecycle, Resumption & Abandonment

#### 1. Objective
Ensure assessment attempts have a complete lifecycle: allow candidates to detect and resume incomplete assessments, gracefully abandon an assessment if desired, and prevent stale attempts from blocking progress.

#### 2. Existing Code / Files to Reuse
- `backend/questions/models.py` (`AssessmentAttempt`, `AttemptStatus`).
- `backend/questions/assessment_views.py` (`MCQAssessmentStartView`, `CodingAssessmentStartView`, `get_attempt_for_request`).
- `frontend/templates/assessments/my_attempts.html`.
- `frontend/templates/dashboard.html`.

#### 3. Files to Create / Modify
- **[MODIFY]** [`backend/questions/assessment_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_views.py):
  - Add `AssessmentAbandonView` (`POST /api/assessments/<attempt_id>/abandon/`).
  - Add `ActiveAssessmentAttemptView` (`GET /api/assessments/active/`).
  - Enhance `get_attempt_for_request`: check if attempt timer has expired (`is_time_expired`). If expired and `IN_PROGRESS`, set `submitted_at = now` and handle timeout state cleanly.
- **[MODIFY]** [`backend/questions/assessment_urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_urls.py):
  - Register `path('<int:attempt_id>/abandon/', AssessmentAbandonView.as_view(), name='assessment_abandon')`.
  - Register `path('active/', ActiveAssessmentAttemptView.as_view(), name='assessment_active')`.
- **[MODIFY]** [`frontend/templates/assessments/my_attempts.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/my_attempts.html):
  - In the table action column:
    - If status is `COMPLETED`, show "View Result".
    - If status is `IN_PROGRESS` and timer not expired, show "Resume" (links to `/assessments/mcq/<id>/` or `/coding/assessment/<id>/`) and "Abandon" button.
    - If status is `ABANDONED`, show badge `Abandoned` (disabled).
- **[MODIFY]** [`frontend/templates/dashboard.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/dashboard.html):
  - Add an "Active Assessment Alert" card if `/api/assessments/active/` returns an active attempt, prompting the candidate: *"You have an active [MCQ/Coding] assessment in progress. [Resume Assessment] or [Abandon]"*.
- **[MODIFY]** [`frontend/templates/assessments/mcq_setup.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/mcq_setup.html) & [`frontend/templates/assessments/coding_setup.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/coding_setup.html):
  - Check for existing active attempt before starting; prompt user with options to resume or start fresh.

#### 4. API Endpoints & Contracts

##### Endpoint B1: `POST /api/assessments/<int:attempt_id>/abandon/`
- **Access**: Attempt Owner (Student via JWT or Guest via `session_id`)
- **Validation**: Attempt must exist, belong to requester, and currently have `status == AttemptStatus.IN_PROGRESS`.
- **Action**: Transitions `status` to `AttemptStatus.ABANDONED` and sets `submitted_at = timezone.now()`.
- **Response `200 OK`**:
  ```json
  {
    "status": "success",
    "message": "Assessment attempt has been abandoned.",
    "attempt_id": 18,
    "attempt_status": "ABANDONED"
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: Attempt is already `COMPLETED` or `ABANDONED`.
  - `403 Forbidden`: Requester is not the owner of the attempt.
  - `404 Not Found`: Attempt does not exist.

##### Endpoint B2: `GET /api/assessments/active/`
- **Access**: Student via JWT or Guest via `?session_id=`
- **Action**: Queries for the most recent `AssessmentAttempt` where `status == IN_PROGRESS` and `started_at + time_limit_seconds > now()`.
- **Response `200 OK` (Active Attempt Exists)**:
  ```json
  {
    "has_active_attempt": true,
    "attempt": {
      "id": 18,
      "question_type": "CODE",
      "category": "Python",
      "difficulty": "EASY",
      "remaining_seconds": 1420,
      "resume_url": "/coding/assessment/18/"
    }
  }
  ```
- **Response `200 OK` (No Active Attempt)**:
  ```json
  {
    "has_active_attempt": false,
    "attempt": null
  }
  ```

#### 5. Database Changes
- **None**. `AttemptStatus.ABANDONED` is already defined in `AssessmentAttempt.status`.

#### 6. Scoring & Integrity
- Abandoned attempts are **never** included in Unified Score calculations, Leaderboards, or Category Mastery aggregations (`status=COMPLETED` filter is strictly preserved).

---

### MODULE 11C — Solution Review Utilities & Admin Data Export

#### 1. Objective
Enhance the candidate post-assessment experience with solution utilities (Copy Solution, Download `.py`/`.java`/`.cpp` file, Practice Again CTA) and equip administrators with CSV report exports for attempts and analytics.

#### 2. Existing Code / Files to Reuse
- `frontend/templates/assessments/coding_result.html`.
- `backend/questions/analytics_views.py` (`AdminAnalyticsView`).
- `frontend/templates/admin/analytics.html`.

#### 3. Files to Create / Modify
- **[MODIFY]** [`frontend/templates/assessments/coding_result.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/coding_result.html):
  - Add "Copy Code" button next to the submitted code card with visual toast: *"Solution copied to clipboard!"*.
  - Add "Download Code" button dynamically saving file with appropriate extension (`.py`, `.java`, `.cpp`).
  - Add "Practice Again" CTA button linking to `/coding/setup/?problem_id=<id>` to quickly retry.
- **[MODIFY]** [`backend/questions/analytics_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/analytics_views.py):
  - Add `AdminAnalyticsExportView` (`GET /api/admin/analytics/export/?format=csv`).
  - Strict `IsAdmin` permission.
  - Streams/returns CSV formatted assessment records:
    `Attempt ID, Student Username, Email, Type, Category, Difficulty, Score, Max Score, Percentage, Status, Started At, Submitted At`.
- **[MODIFY]** [`backend/questions/assessment_urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_urls.py) or [`backend/config/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/urls.py):
  - Register `path('api/admin/analytics/export/', AdminAnalyticsExportView.as_view(), name='api_admin_analytics_export')`.
- **[MODIFY]** [`frontend/templates/admin/analytics.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/admin_dashboard/analytics.html):
  - Add "Export Attempts (CSV)" button in the page header triggering the download.
  - Render "Top Hardest Questions" diagnostic card based on existing `top_failed_questions` API data.

#### 4. API Endpoints & Contracts

##### Endpoint C1: `GET /api/admin/analytics/export/?format=csv`
- **Access**: Strictly `IsAdmin` (HTTP 403 for students, 401 for guests).
- **Response Headers**:
  - `Content-Type: text/csv; charset=utf-8`
  - `Content-Disposition: attachment; filename="skillbyte_assessment_report_<date>.csv"`
- **Response Body**:
  ```csv
  Attempt ID,Student Username,Email,Assessment Type,Category,Difficulty,Score,Max Score,Percentage,Status,Started At,Submitted At
  101,alice_phase10,alice@skillbyte.phase10,MCQ,Python,EASY,18.0,20,90.0%,COMPLETED,2026-09-23 10:00:00,2026-09-23 10:08:30
  102,alice_phase10,alice@skillbyte.phase10,CODE,DSA,EASY,30.0,30,100.0%,COMPLETED,2026-09-23 10:15:00,2026-09-23 10:32:10
  ```

#### 5. Database Changes
- **None**. Reads from existing `AssessmentAttempt`, `AssessmentResult`, `User` records.

---

### MODULE 11D — Platform Reliability & Security Hardening

#### 1. Objective
Ensure the platform fails gracefully with branded error pages (404, 403, 500) and protects sensitive authentication and code execution APIs from abuse using scoped DRF rate limiting.

#### 2. Existing Code / Files to Reuse
- `backend/config/settings.py` (`REST_FRAMEWORK` configuration).
- `backend/config/urls.py` (`handler404`, `handler500`, `handler403`).
- `backend/api/views.py`.
- `frontend/static/css/main.css`.

#### 3. Files to Create / Modify
- **[NEW]** `frontend/templates/404.html`:
  - Branded "404 — Page Not Found" with glassmorphism layout, helpful message, and "Return to Home / Dashboard" button.
- **[NEW]** `frontend/templates/403.html`:
  - Branded "403 — Access Denied" explaining insufficient permissions (e.g. Administrator privileges required) with "Return to Dashboard" button.
- **[NEW]** `frontend/templates/500.html`:
  - Branded "500 — Server Error" reassurance page.
- **[MODIFY]** [`backend/api/views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/api/views.py):
  - Implement `custom_404_view(request, exception=None)`, `custom_403_view(request, exception=None)`, and `custom_500_view(request)`.
- **[MODIFY]** [`backend/config/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/urls.py):
  - Set `handler404 = 'api.views.custom_404_view'`.
  - Set `handler403 = 'api.views.custom_403_view'`.
  - Set `handler500 = 'api.views.custom_500_view'`.
- **[MODIFY]** [`backend/config/settings.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/settings.py):
  - Configure DRF throttling:
    ```python
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/minute',
        'user': '1200/minute',
        'auth_attempt': '15/minute',
        'code_run': '30/minute',
    }
    ```
- **[MODIFY]** [`backend/accounts/views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/views.py) and [`backend/questions/assessment_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_views.py):
  - Add `throttle_scope = 'auth_attempt'` to `LoginView` and `RegisterView`.
  - Add `throttle_scope = 'code_run'` to `CodingAssessmentRunCodeView`.

#### 4. Automated Test Safety
- Ensure test runner (`TESTING = 'test' in sys.argv`) does not throttle automated unit tests (e.g. disable throttles in `settings.py` when `TESTING` is active).

---

## D. Automated Test Plan for Phase 11

A dedicated test suite `backend/questions/tests_phase11.py` and additions in `backend/accounts/tests.py` will validate all new capabilities:

### Test Suite: `questions.tests_phase11` (12 tests)
1. `test_student_update_profile_success`: `PATCH /api/auth/me/` updates first/last name.
2. `test_student_update_profile_duplicate_email`: Rejects duplicate email with HTTP 400.
3. `test_student_change_password_success`: Verifies old password and authenticates with new password.
4. `test_student_change_password_invalid_current`: Rejects wrong current password with HTTP 400.
5. `test_student_change_password_mismatch`: Rejects mismatched new passwords.
6. `test_abandon_active_attempt_success`: Marks attempt as `ABANDONED` and records `submitted_at`.
7. `test_abandon_completed_attempt_rejected`: Rejects abandoning an already completed attempt (HTTP 400).
8. `test_abandon_unowned_attempt_forbidden`: Rejects abandoning another user's attempt (HTTP 403).
9. `test_active_attempt_detection`: Detects unexpired `IN_PROGRESS` attempt.
10. `test_admin_analytics_csv_export_authorized`: Admin receives CSV file with correct headers.
11. `test_admin_analytics_csv_export_student_denied`: Student receives HTTP 403 on CSV export.
12. `test_custom_error_handlers`: 404, 403, and 500 render custom branded HTML templates.

### Regression Test Suite Execution
- `python manage.py test questions.tests_phase10` (11 tests)
- `python manage.py test questions.tests_phase9` (15 tests)
- `python manage.py test questions.tests` (16 tests)
- `python manage.py test accounts` (14 tests)
- Total tests passing requirement: **68+ tests (100% PASS)**.

---

## E. Chrome Browser CDP Verification Plan

1. **Profile & Settings (`/profile/`)**:
   - Log in as student `alice_phase10`.
   - Open `/profile/`; verify student card, Unified Score badge, and details load.
   - Update first name to "Alicia" and submit; verify updated name appears in navbar and profile.
   - Test password change form with mismatched passwords; verify error alert.
   - Change password successfully.
2. **Navbar Polish**:
   - Log in as admin `phase10_admin`; verify "Question Bank" appears **only once** in navbar.
   - Verify "Profile" link is visible and navigates to `/profile/`.
   - Test mobile viewport (width 375px); verify hamburger collapse toggles smoothly.
3. **Assessment Resumption & Abandonment**:
   - Start an assessment; verify `/api/assessments/active/` returns active attempt.
   - Navigate to `/dashboard/`; verify active attempt banner displays with "Resume" and "Abandon" buttons.
   - Click "Resume"; verify it opens assessment workspace with timer intact.
   - Click "Abandon"; verify attempt transitions to `ABANDONED` and banner disappears.
4. **Coding Solution Review Utilities**:
   - Open `/coding/result/17/`.
   - Click "Copy Code"; verify clipboard contents.
   - Click "Download Solution"; verify file download (`solution.py`).
   - Click "Practice Again"; verify redirect to coding setup.
5. **Admin CSV Export**:
   - Log in as admin; navigate to `/admin/analytics/`.
   - Click "Export CSV Report"; verify download of valid CSV data.
6. **Custom Error Pages**:
   - Navigate to `http://127.0.0.1:8000/non-existent-page-test/`.
   - Verify branded 404 error page renders with "Return to Home" button.
7. **Console Health**:
   - Verify **0 console errors** across all interactions.

---

## F. Acceptance Criteria & Definition of Done

### Acceptance Criteria
- [ ] Student can update name and email via `/profile/` and `/api/auth/me/`.
- [ ] Student can securely change password via `/api/auth/change-password/`.
- [ ] Duplicate "Question Bank" link in navbar is eliminated.
- [ ] Mobile navbar toggler functions smoothly on small viewports.
- [ ] In-progress assessments can be resumed from Dashboard/History or cleanly abandoned via API.
- [ ] Abandoned attempts do not pollute score calculations or leaderboards.
- [ ] Coding Results page provides Copy Code, Download Code, and Practice Again CTA.
- [ ] Admin Analytics page provides CSV report download.
- [ ] Custom branded 404, 403, and 500 error pages display properly.
- [ ] Scoped rate limiting protects login, registration, and Judge0 code execution.

### PHASE 11 DEFINITION OF DONE
1. `python manage.py check` **PASS** (0 issues, 0 silenced)
2. All new Phase 11 automated tests **PASS** (12/12)
3. Phase 10 regression tests **PASS** (11/11)
4. Phase 9 regression tests **PASS** (15/15)
5. Base question regression tests **PASS** (16/16)
6. Accounts regression tests **PASS** (14/14)
7. Total automated tests passing: **68 / 68 (100% PASS)**
8. Chrome CDP Browser verification **PASS** across all 7 workflows
9. Browser console errors: **0 recorded**
10. Database integrity post-test audit: **PASS**
11. Git checkpoint created on `main` with clean working tree.

