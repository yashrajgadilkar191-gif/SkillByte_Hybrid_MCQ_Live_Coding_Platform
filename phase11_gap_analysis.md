# SKILLBYTE — Phase 11 Gap Analysis & Requirements Traceability Matrix

> **Project**: SkillByte — *"Where Theory Meets Practice"*  
> **Source of Truth**: SkillByte System Requirements Specification (SRS) & Architecture Documents  
> **Date**: September 23, 2026  
> **Author**: Lead Full-Stack Developer  
> **Status**: Planning Stage (No application code modified)

---

## 1. Executive Summary & Verification State (Phases 1–10)

The **SKILLBYTE** platform has successfully completed and verified Phases 1 through 10:
- **Django System Check**: `PASS (0 issues)`
- **Automated Regression Test Suite**: `56/56 PASS (100%)`
  - `questions.tests_phase10`: 11/11 PASS
  - `questions.tests_phase9`: 15/15 PASS
  - `questions.tests` (Base): 16/16 PASS
  - `accounts.tests`: 14/14 PASS
- **Chrome CDP Browser Suite**: `PASS across all 6 end-to-end scenarios`
- **Browser Console Errors**: `0 errors recorded`
- **Database Integrity**: `Verified across PostgreSQL`
- **Git Checkpoint**: `3da6acb` on `main` (working tree clean)

---

## 2. Comprehensive Requirements Matrix & Status

| SRS Requirement Area | Status | Completed In | Incomplete / Gaps for Phase 11 |
| :--- | :---: | :---: | :--- |
| **1. Project Foundation & DB** | **Complete** | Phase 1 | None. Exclusive PostgreSQL, Django 5.2, DRF, JWT. |
| **2. Authentication & RBAC** | **Substantially Complete** | Phase 2 | Profile updating, password changing, profile UI. |
| **3. Core Question Bank Schema** | **Complete** | Phase 3 | None. Unified `Question`, `QuestionOption`, `TestCase`. |
| **4. MCQ Assessment Engine** | **Complete** | Phase 4 | None. Timer, randomization, scoring, review cards. |
| **5. Monaco Coding Workspace** | **Complete** | Phase 5, 10 | Live Run Code, syntax highlighting, language switch. |
| **6. Judge0 Code Execution** | **Complete** | Phase 6 | None. Dockerized sandboxing, partial credit scoring. |
| **7. Coding Results & Evaluation UI** | **Complete** | Phase 7 | Code copy/download utilities, re-attempt flow. |
| **8. Attempt History & Progress** | **Complete** | Phase 8, 10 | In-progress attempt resumption from history. |
| **9. Admin Question Bank & Test Cases**| **Complete** | Phase 9 | None. Full CRUD, safe delete, active toggling. |
| **10. Category-wise Leaderboard** | **Complete** | Phase 10 | None. Public access, best-score deduplication, podium. |
| **11. Unified Scoring & Mastery** | **Complete** | Phase 10 | None. Best score per unique question, skill tiers. |
| **12. Admin Platform Analytics** | **Substantially Complete** | Phase 10 | CSV data export, question diagnostic drilldown. |
| **13. Assessment Lifecycle & Resilience**| **Partially Complete** | Phase 4, 5 | Explicit abandon endpoint, active attempt resumption. |
| **14. Platform UX & Reliability** | **Partially Complete** | Phase 1–10 | Custom 404/403/500 pages, API throttling, navbar fix. |

---

## 3. Detailed Gap Analysis by Area

---

### Gap 1: Student Profile Editing, Password Change & Profile Page

- **SRS Requirement / Reference**:  
  *SRS Section on User Management & Account Security*:  
  "Registered students shall be able to view their profile, update their personal details (first name, last name), and securely change their account password. The system must enforce strong password criteria and invalidate stale sessions where appropriate."
- **Current Implementation Status**:  
  **Partially Complete (Read-Only)**
- **Evidence from the Current Codebase**:  
  - In [`backend/accounts/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/urls.py) and [`backend/accounts/views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/accounts/views.py), only `CurrentUserView` (`GET /api/auth/me/`) is implemented.
  - There is no `PUT` or `PATCH` handler on `/api/auth/me/` or a dedicated profile update view.
  - There is no password change endpoint (`POST /api/auth/change-password/`) validating old passwords against PBKDF2 hashes.
  - There is no dedicated `/profile/` or `/settings/` frontend template. Clicking the user's name in the navbar does not open an account management page.
- **What is Missing**:  
  1. `UserProfileUpdateView` supporting `PUT`/`PATCH` to update first name, last name, and email.
  2. `ChangePasswordView` verifying current password and setting new password using Django's `validate_password`.
  3. Student Profile page (`frontend/templates/profile.html` or `/settings/`) displaying student details, registration date, unified score badge, and password change modal.
- **Priority**: **High**
- **Suggested Module**: **Module 11A — Student Profile & Account Management**

---

### Gap 2: In-Progress Assessment Resumption, Tab Recovery & Abandonment

- **SRS Reference**:  
  *SRS Assessment Session Lifecycle*:  
  "Assessment sessions must handle unexpected client dropouts or accidental tab closures. Candidates must be permitted to resume active tests within the remaining timer window, or explicitly abandon an incomplete attempt to prevent orphaned states."
- **Current Implementation Status**:  
  **Incomplete / Unhandled Edge Case**
- **Evidence from the Current Codebase**:  
  - In [`backend/questions/models.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/models.py) line 38, `AttemptStatus.ABANDONED = 'ABANDONED'` is defined in choices, but is never used anywhere in views or services.
  - In [`backend/questions/assessment_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/assessment_views.py):
    - `MCQAssessmentStartView` and `CodingAssessmentStartView` always create a new `AssessmentAttempt`. If a student already has an `IN_PROGRESS` attempt for that category/question, the system does not prompt them to resume.
    - There is no endpoint to abandon an attempt (e.g. `POST /api/assessments/<id>/abandon/`).
    - If a candidate navigates away or closes the tab, the attempt remains `IN_PROGRESS` indefinitely in PostgreSQL.
  - In [`frontend/templates/assessments/my_attempts.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/my_attempts.html):
    - The action column only renders a "View Result" button. For `IN_PROGRESS` attempts, clicking this leads to a blank or invalid result page instead of a "Resume Assessment" action.
- **What is Missing**:  
  1. Abandon endpoint: `POST /api/assessments/<attempt_id>/abandon/` marking attempt as `ABANDONED`.
  2. Active attempt detection on setup pages: notify the candidate if they have an active attempt and offer to resume or abandon.
  3. "Resume Assessment" button in `my_attempts.html` and `dashboard.html` for `IN_PROGRESS` attempts with active timers.
  4. Server-side auto-expiry: automatically treat attempts past `started_at + time_limit_seconds` as expired when accessed.
- **Priority**: **High**
- **Suggested Module**: **Module 11B — Assessment Lifecycle, Resumption & Abandon Management**

---

### Gap 3: Navbar Redundancy & UI/UX Harmonization

- **SRS Reference**:  
  *SRS Navigation & Accessibility*:  
  "Navigation elements must adapt cleanly to user authentication states and roles without duplicate links, ensuring intuitive navigation across devices."
- **Current Status**:  
  **Partially Complete (Contains UI Bug)**
- **Evidence from the Current Codebase**:  
  - In [`frontend/static/js/auth.js`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/static/js/auth.js) lines 143–153:
    ```javascript
    const adminLink = user?.role === 'ADMIN' ? `<a href="/admin/questions/" ...>Question Bank</a>` : '';
    const adminLinks = user?.role === 'ADMIN' ? `
        <a href="/admin/questions/" ...>Question Bank</a>
        <a href="/admin/analytics/" ...>Analytics</a>
    ` : '';
    authNav.innerHTML = `
        ...
        ${adminLink}
        ${adminLinks}
    `;
    ```
    For users with `role === 'ADMIN'`, the "Question Bank" button is rendered **twice** in the navbar.
  - In [`frontend/templates/base.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/base.html), the static navbar does not include a responsive hamburger collapse button for small/mobile screen widths, causing navbar buttons to wrap awkwardly on mobile viewports.
- **What is Missing**:  
  1. Remove duplicate `${adminLink}` in `auth.js`.
  2. Add Profile link in student navbar dropdown or menu.
  3. Implement responsive Bootstrap navbar toggler (`navbar-toggler`) in `base.html`.
- **Priority**: **Medium**
- **Suggested Module**: **Module 11A — Navbar Harmonization & UI Polish**

---

### Gap 4: Solution Utilities on Coding Results (Copy Code, Download Solution & Re-attempt Flow)

- **SRS Reference**:  
  *SRS Coding Post-Assessment Features*:  
  "Upon viewing evaluation results, candidates shall be provided with utilities to copy their submitted solution to the clipboard, download the source file in the appropriate language extension, and quickly re-attempt the problem to improve their score."
- **Current Implementation Status**:  
  **Partially Complete**
- **Evidence from the Current Codebase**:  
  - In [`frontend/templates/assessments/coding_result.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/assessments/coding_result.html):
    - Submitted code is shown inside a `<pre><code>` block, but there is no "Copy Code" button or "Download Source File" button.
    - There is no direct "Try Again / Re-attempt" action linking back to `/coding/setup/` or `/coding/assessment/<new_attempt>/`.
- **What is Missing**:  
  1. "Copy Code" button with visual feedback (tooltip/toast: "Copied!").
  2. "Download Solution" button triggering a download named `solution.<ext>` (`.py`, `.java`, `.cpp`).
  3. "Practice Again" CTA button that creates a new assessment attempt for that specific problem.
- **Priority**: **Medium**
- **Suggested Module**: **Module 11C — Solution Review Utilities & Practice Flow**

---

### Gap 5: Admin Analytics Data Export & Question Diagnostics Drilldown

- **SRS Reference**:  
  *SRS Administrator Analytics & Reporting*:  
  "Administrators shall be able to export assessment metrics and attempt records for institutional reporting, and view diagnostic data on questions with the lowest pass rates or frequent compilation errors."
- **Current Implementation Status**:  
  **Partially Complete (Dashboard verified in Phase 10; Export not yet implemented)**
- **Evidence from the Current Codebase**:  
  - In [`backend/questions/analytics_views.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/analytics_views.py) and [`frontend/templates/admin/analytics.html`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/frontend/templates/admin_dashboard/analytics.html):
    - Executive KPIs, verdict counts, and category performance are implemented.
    - However, there is no CSV/Excel export endpoint for administrators to download attempt records or student score rosters.
    - While `top_failed_questions` is computed in the backend, the Admin Analytics UI does not yet render a dedicated "Diagnostic: Questions Needing Review" panel.
- **What is Missing**:  
  1. Endpoint `GET /api/admin/analytics/export/?format=csv` (strictly guarded by `IsAdmin`) providing a downloadable CSV of completed attempts and performance summaries.
  2. "Export CSV Report" button on the Admin Analytics page.
  3. Diagnostic panel displaying questions with the highest failure rates on the analytics dashboard.
- **Priority**: **Medium**
- **Suggested Module**: **Module 11C — Admin Reporting & Export Tools**

---

### Gap 6: Custom Branded Error Pages (404, 403, 500)

- **SRS Reference**:  
  *SRS Error Handling & User Experience*:  
  "All HTTP error responses (404 Not Found, 403 Forbidden, 500 Internal Server Error) must be handled gracefully with customized pages maintaining the platform's visual identity, navigation links, and friendly remediation guidance."
- **Current Implementation Status**:  
  **Incomplete**
- **Evidence from the Current Codebase**:  
  - Currently, accessing a nonexistent URL (e.g. `/invalid-url/`) returns standard Django debug pages or plain server messages.
  - There are no custom templates `404.html`, `403.html`, or `500.html` in `frontend/templates/`.
  - [`backend/config/urls.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/urls.py) does not define custom handlers (`handler404`, `handler500`, `handler403`).
- **What is Missing**:  
  1. `frontend/templates/404.html`: Friendly "Page Not Found" screen with search and "Return Home" CTA.
  2. `frontend/templates/403.html`: Clear "Access Denied" screen explaining role requirements.
  3. `frontend/templates/500.html`: Clean "Server Error" screen reassuring users and providing support contact.
  4. Custom handlers configured in `backend/config/urls.py` and `backend/api/views.py`.
- **Priority**: **Medium**
- **Suggested Module**: **Module 11D — Platform Reliability & Custom Error Handlers**

---

### Gap 7: API Throttling & Security Rate Limiting

- **SRS Reference**:  
  *SRS Security & Availability*:  
  "Authentication endpoints and resource-intensive code execution endpoints must be protected against brute-force attacks and denial-of-service attempts via rate-limiting mechanisms."
- **Current Implementation Status**:  
  **Incomplete**
- **Evidence from the Current Codebase**:  
  - In [`backend/config/settings.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/config/settings.py), `REST_FRAMEWORK` does not configure `DEFAULT_THROTTLE_CLASSES` or `DEFAULT_THROTTLE_RATES`.
  - Endpoints such as `POST /api/auth/login/`, `POST /api/auth/register/`, and `POST /api/assessments/coding/<id>/run/` have no throttling guards. A rogue script could flood Judge0 or PostgreSQL.
- **What is Missing**:  
  1. Add scoped throttling in `settings.py`:
     - `auth`: e.g. 10 requests / minute for login/register.
     - `coding_run`: e.g. 15 requests / minute per student for live code execution.
     - `anon`: e.g. 60 requests / minute for unauthenticated browsing.
  2. Attach throttle classes to `LoginView`, `RegisterView`, and `CodingAssessmentRunCodeView`.
- **Priority**: **Medium**
- **Suggested Module**: **Module 11D — Security Hardening & Rate Limiting**

---

### Gap 8: Multi-Language Starter Code Standardization

- **SRS Reference**:  
  *SRS Coding Languages & Starter Templates*:  
  "Every coding problem must provide validated, syntactically correct starter code for all three supported languages: Python, Java, and C++."
- **Current Implementation Status**:  
  **Partially Complete**
- **Evidence from the Current Codebase**:  
  - In [`backend/questions/management/commands/seed_questions.py`](file:///c:/Users/Ambition/Desktop/Projects/MiniProject/backend/questions/management/commands/seed_questions.py), some seeded coding questions only provide `starter_code: {"python": "..."}` without curated boilerplate for Java (`public class Solution`) or C++ (`#include <iostream>`).
  - While the frontend fallback provides basic templates, database questions should possess complete multilingual starter definitions.
- **What is Missing**:  
  1. Update `seed_questions.py` so all coding problems include well-formatted starter code for `python`, `java`, and `cpp`.
- **Priority**: **Low**
- **Suggested Module**: **Module 11C — Seed Data & Content Standardization**

---

## 4. Future-Scope Features (Explicitly OUT OF SCOPE for SRS Baseline)

The following features belong to future roadmap iterations and must **NOT** be treated as mandatory SRS requirements for SkillByte:
1. **Live Collaborative Multi-User Coding**: WebRTC / WebSocket pair programming.
2. **AI Proctoring & Webcam / Screen Tracking**: Facial recognition or tab-switching AI monitors.
3. **Plagiarism Detection Engine**: AST-based code similarity matching across students.
4. **Social OAuth2 Authentication**: Google, GitHub, or LinkedIn third-party logins.
5. **Payment Gateway / Monetization**: Paid certification tracks or subscription tiers.
6. **Native Mobile App**: Native iOS or Android packages.

---

## 5. Recommended Scope for Phase 11

To complete all remaining non-future SRS requirements and achieve an institutional, production-grade release of **SKILLBYTE**, Phase 11 should be structured into four targeted modules:

### Module 11A: Student Profile & Account Security Management
- Profile management API (`GET / PUT / PATCH /api/auth/me/`)
- Change password API (`POST /api/auth/change-password/`)
- Glassmorphism Student Profile & Settings page (`/profile/`)
- Navbar cleanup: eliminate duplicate "Question Bank" button and add Profile link

### Module 11B: Assessment Lifecycle, Resumption & Abandonment
- Abandon attempt API (`POST /api/assessments/<attempt_id>/abandon/`)
- In-progress attempt detection & seamless resumption flow from Dashboard and Attempts pages
- Server-side auto-expiry for expired attempts

### Module 11C: Solution Review Utilities & Admin Data Export
- "Copy Code" & "Download Solution" (`.py`, `.java`, `.cpp`) on Coding Results
- "Practice Again" quick re-attempt flow
- Admin CSV Report Export endpoint (`GET /api/admin/analytics/export/`) & UI trigger

### Module 11D: Platform Reliability, Custom Error Pages & Security Throttling
- Custom branded `404.html`, `403.html`, and `500.html` error pages
- Django custom error handlers (`handler404`, `handler500`, `handler403`)
- DRF scoped rate limiting on authentication and Judge0 execution endpoints

