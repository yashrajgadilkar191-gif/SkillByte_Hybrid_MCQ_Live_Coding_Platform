
# SKILLBYTE — "Where Theory Meets Practice"

[![Release: v1.0.0-final-release](https://img.shields.io/badge/Release-v1.0.0--final--release-blue.svg)](https://github.com/your-org/skillbyte)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Django: 4.2+ LTS](https://img.shields.io/badge/Django-4.2%2B%20LTS-darkgreen.svg)](https://www.djangoproject.com/)
[![PostgreSQL: 15+](https://img.shields.io/badge/PostgreSQL-15%2B%20Exclusive-blue.svg)](https://www.postgresql.org/)
[![Judge0: Sandboxed](https://img.shields.io/badge/Code%20Execution-Judge0%20Docker-orange.svg)](https://judge0.com/)
[![Tests: 68/68 PASS](https://img.shields.io/badge/Tests-68%2F68%20PASS%20(100%25)-success.svg)](file:///docs/TESTING_REPORT.md)
[![CDP: 10/10 PASS](https://img.shields.io/badge/Chrome%20CDP-10%2F10%20(0%20Errors)-success.svg)](file:///docs/TESTING_REPORT.md)
[![SRS Compliance: 42/42](https://img.shields.io/badge/SRS%20Compliance-42%2F42%20(100%25)-success.svg)](file:///docs/FINAL_PROJECT_REPORT.md)

**SKILLBYTE** is a production-grade, hybrid technical skill assessment platform engineered for university examinations, campus recruitments, and corporate technical evaluations. It unifies:
1. **Theoretical MCQ Assessments** (General Knowledge, English, Mathematics) with server-authoritative timer validation and instant solution breakdowns.
2. **Live In-Browser Coding Assessments** (Python, Java, C++, DSA) powered by Microsoft’s Monaco Editor (the editor core of VS Code) and an isolated, containerized Judge0 execution engine.
3. **Unified Gamification & Anti-Farming Deduplication**: A **Best Score per Unique Question** mathematical scoring model that prevents point farming and dynamically assigns students into skill tiers (*Novice*, *Apprentice*, *Specialist*, *Master*).
4. **Administrative Governance & Analytics**: Full Question Bank CRUD, hidden test case management, macro-level KPI dashboards, and one-click server-side CSV data streaming.

---

## Academic Project Information

- **Institution**: `[COLLEGE_NAME]`, Department of `[DEPARTMENT_NAME]`
- **Project Team**: `[STUDENT_NAME_1]` (`[ROLL_NUMBER_1]`), `[STUDENT_NAME_2]` (`[ROLL_NUMBER_2]`)
- **Faculty Guide**: `[PROJECT_GUIDE_NAME]`, `[DESIGNATION_OF_GUIDE]`
- **Academic Year**: `[ACADEMIC_YEAR]`
- **Final Release Tag**: `v1.0.0-final-release` (Anchored at Commit `9e66eef`)

---

## 1. Documentation Index (`docs/`)

All formal academic, architectural, and operational specifications are available in the [`docs/`](docs/) directory:

| Document ID | File Path | Focus Area & Description |
|:---:|---|---|
| **DELIV-01** | [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) | Multi-tier architecture blueprint, Mermaid component & sequence diagrams. |
| **DELIV-02** | [`docs/DATABASE_ER_DIAGRAM.md`](docs/DATABASE_ER_DIAGRAM.md) | Complete Entity-Relationship diagram across all 9 models & data dictionary. |
| **DELIV-03** | [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) | Exhaustive REST API specification covering all 28 endpoints and schemas. |
| **DELIV-04** | [`docs/TESTING_REPORT.md`](docs/TESTING_REPORT.md) | Quality assurance report: 68 automated tests, 10 CDP browser scenarios, 0 errors. |
| **DELIV-05** | [`docs/SECURITY_DOCUMENTATION.md`](docs/SECURITY_DOCUMENTATION.md) | Security architecture, PBKDF2 hashing, JWT blacklisting, RBAC, Judge0 cgroups, STRIDE. |
| **DELIV-06** | [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) | Production Linux operations manual (Gunicorn, Nginx, PostgreSQL, SSL Certbot, Docker). |
| **DELIV-07** | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | Synchronized, timed 12-minute presenter script and contingency runbook. |
| **DELIV-08** | [`docs/VIVA_PREPARATION_GUIDE.md`](docs/VIVA_PREPARATION_GUIDE.md) | Oral defense manual featuring 25 technical examiner questions with model answers. |
| **DELIV-09** | [`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) | Comprehensive 32-chapter academic capstone project report. |
| **DELIV-10** | [`docs/FINAL_PRESENTATION_SLIDES.md`](docs/FINAL_PRESENTATION_SLIDES.md) | 16-slide academic presentation specification with visual layouts and speaker notes. |

---

## 2. Key Features Across All 11 Engineering Phases

### 2.1 Core Authentication & Role Management (Phases 1–2, 11)
- **PBKDF2 Password Hashing**: Hashed using 600,000 SHA-256 iterations with unique cryptographic salt per user.
- **Stateless JWT Authentication**: Access tokens (60 min) and rotated Refresh tokens (7 days) via SimpleJWT.
- **Token Blacklisting**: Logout and token refresh immediately blacklist previous refresh tokens in PostgreSQL, thwarting replay attacks.
- **Three-Tier RBAC**: Granular permissions distinguishing `ADMIN`, `STUDENT`, and `GUEST`.
- **Student Profile Management**: Real-time profile editing (`PATCH /api/auth/me/`) and secure password change workflows.

### 2.2 Question Bank & Theoretical MCQ Engine (Phases 3–4, 9)
- **Unified Relational Schema**: Single model structure supporting both MCQ theoretical questions and practical coding challenges.
- **Categorization**: Theoretical subjects (General Knowledge, English, Mathematics) and Coding domains (Python, Java, C++, DSA).
- **Server-Authoritative Timer**: Timestamps recorded upon initiation (`started_at`); submissions strictly validated upon completion.
- **Zero-Leakage Data Sanitization**: Correct answer flags (`is_correct`) are stripped server-side from student serializers during active exams.
- **Instant Result Analytics**: Immediate post-exam scoring with question-by-question review cards and detailed explanations.

### 2.3 Live Monaco Coding Environment (Phases 5–7, 10, 11)
- **In-Browser Desktop IDE**: Microsoft Monaco Editor (v0.34+) loaded asynchronously with dark/light themes, syntax highlighting, and minimap.
- **Multi-Language Support**: Pre-loaded starter code templates for Python 3, Java (OpenJDK), and C++ (GCC).
- **"Run Code" Diagnostics**: Instant candidate testing against public sample test cases with real-time stdout/stderr console feedback.
- **"Submit Solution" Grading**: Comprehensive grading against hidden test cases (`is_hidden=True`) evaluated in Judge0.
- **Failure Classification**: Automatic tagging of `ACCEPTED`, `PARTIAL`, `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED` (TLE), `RUNTIME_ERROR` (RTE), and `COMPILATION_ERROR` (CE).
- **Candidate Utility Tools**: One-click **Copy Solution** (with UI toast), native source file **Download** (`.py`, `.java`, `.cpp`), and **Practice Again** session resets.

### 2.4 Containerized Code Execution via Judge0 (Phases 6–7)
- **Self-Hosted Sandboxing**: Runs as an isolated microservice on port `2358` via Docker Compose.
- **Linux Control Groups (cgroups)**: Enforces hard resource ceilings (2.0s CPU time limit, 256 MB RAM ceiling, 64 PID ceiling).
- **Unprivileged Execution**: Code executes as user `nobody` (UID 65534) with read-only root filesystems.
- **Zero Egress Networking**: Container sockets are launched with `--net none`, completely blocking outbound network connections, DDoS attempts, and SSRF attacks.

### 2.5 Unified Scoring, Gamification & Leaderboard (Phase 10)
- **Best Score per Unique Question**: Deduplication algorithm prevents score farming. Cumulative points reflect breadth of knowledge rather than repetitive attempts on easy challenges.
- **Dynamic Skill Tiers**: Real-time progression across **Novice** (0–49 pts), **Apprentice** (50–149 pts), **Specialist** (150–299 pts), and **Master** (300+ pts).
- **Two-Dimensional Mastery Tracking**: Student dashboards display Theory Points and Practical Points independently.
- **Dynamic Leaderboards**: Filter rankings by subject and timeframe (All-Time, Monthly, Weekly) without corrupting historical records.

### 2.6 Resilience, Admin Governance & Institutional Export (Phases 9, 11)
- **Assessment Resumption**: Active session endpoint (`GET /api/assessments/active/`) detects incomplete attempts and seamlessly restores editor state, code, and remaining time across browser refreshes.
- **Explicit Abandonment**: Candidates can terminate sessions early (`POST /api/assessments/<id>/abandon/`), transitioning status to `ABANDONED` with 0 marks.
- **Full Admin Question Bank CRUD**: Complete administrative interface for authoring questions, options, starter code, and test cases.
- **Macro-Level KPI Analytics**: Real-time dashboard showing candidate counts, completion rates (88.9%), and subject distribution charts.
- **Institutional CSV Streaming**: One-click server-side CSV export (`GET /api/admin/analytics/export/?format=csv`).
- **Production Polish**: Custom branded 404, 403, and 500 error pages; DRF scoped rate limiters (15/min auth, 30/min code run, 120/min anon).

---

## 3. Technology Stack

- **Backend Kernel**: Python 3.10+, Django 4.2+ LTS, Django REST Framework (DRF) 3.14+
- **Authentication**: `djangorestframework-simplejwt` with Token Blacklisting
- **Persistence Tier**: PostgreSQL 15+ (Exclusively via Django ORM; strictly no SQLite fallback per SRS)
- **Code Execution Sandbox**: Self-hosted Judge0 API v1.13 running inside Docker containers with Linux cgroups
- **In-Browser IDE**: Microsoft Monaco Editor v0.34+ (loaded asynchronously via AMD require)
- **Frontend Presentation**: HTML5, CSS3, JavaScript (Vanilla ES6+), Bootstrap 5.3, Bootstrap Icons
- **HTTP / WSGI Runtime**: Gunicorn WSGI Server & Nginx Reverse Proxy (Production) / Django Runserver (Development)

---

## 4. Multi-Tier Architecture

```
[ Browser / Client ] ──(HTTP/1.1 REST + JWT Bearer)──> [ Django Monolith (:8000) ]
  • Monaco Code Editor                                   • SimpleJWT Auth & Blacklist
  • Bootstrap 5.3 Responsive Views                       • RBAC & Rate Throttling
  • Async ES6 Fetch Controllers                          • Deduplicated Scoring
                                                           │              │
                                                Postgres   │              │ HTTP REST
                                                (:5432)    ▼              ▼ (:2358)
                                          [ PostgreSQL 15 DB ]   [ Judge0 Sandbox ]
                                          • ACID Transactions    • Docker Worker Containers
                                          • Relational Schema    • Linux cgroups limits
                                          • JSONB Starter Code   • Severed Network (--net none)
```

---

## 5. REST API Endpoint Reference (28 Endpoints)

| Method | Endpoint Route | RBAC Access | Module & Description |
|:---:|---|:---:|---|
| `POST` | `/api/auth/register/` | Public | Register new student account (default `STUDENT` role) |
| `POST` | `/api/auth/login/` | Public | Authenticate via email/username; obtain JWT tokens |
| `POST` | `/api/auth/token/refresh/` | Public | Refresh expired access token with token rotation |
| `POST` | `/api/auth/logout/` | Authenticated | Blacklist refresh token & terminate session |
| `GET/PUT/PATCH`| `/api/auth/me/` | Authenticated | Retrieve or update user profile and bio |
| `POST` | `/api/auth/change-password/` | Authenticated | Change user account password securely |
| `GET` | `/api/auth/test-student-role/` | Student Only | Verify student RBAC access control |
| `GET` | `/api/auth/test-admin-role/` | Admin Only | Verify administrator RBAC access control |
| `GET` | `/api/questions/` | Public / Student | List active questions with subject & difficulty filters |
| `GET` | `/api/questions/<id>/` | Public / Student | Retrieve sanitized question details |
| `GET` | `/api/assessments/active/` | Student / Guest | Detect active in-progress assessment attempt |
| `POST` | `/api/assessments/<id>/abandon/` | Attempt Owner | Terminate an in-progress assessment session |
| `POST` | `/api/assessments/mcq/start/` | Student / Guest | Initiate a new theoretical MCQ assessment session |
| `POST` | `/api/assessments/mcq/<id>/answer/` | Attempt Owner | Record option selection for an MCQ question |
| `POST` | `/api/assessments/mcq/<id>/submit/` | Attempt Owner | Finalize MCQ assessment and compute official score |
| `GET` | `/api/assessments/mcq/<id>/result/` | Attempt Owner | View score summary and review with explanations |
| `POST` | `/api/assessments/coding/start/` | Student / Guest | Initiate a live coding assessment session |
| `GET` | `/api/assessments/coding/<id>/` | Attempt Owner | Fetch coding problem details and starter code |
| `POST` | `/api/assessments/coding/<id>/run/` | Attempt Owner | Run code against public sample test cases |
| `POST` | `/api/assessments/coding/<id>/submit/` | Attempt Owner | Submit code for hidden test case evaluation in Judge0 |
| `GET` | `/api/assessments/coding/<id>/result/` | Attempt Owner | View code submission telemetry & failure tags |
| `GET` | `/api/assessments/my-attempts/` | Authenticated | Retrieve historical assessment session records |
| `GET` | `/api/assessments/progress/` | Authenticated | Compute unified mastery score & skill tier |
| `GET` | `/api/leaderboard/` | Public / Student | Dynamic leaderboard with category & timeframe filters |
| `GET` | `/api/questions/admin/` | Admin Only | Full CRUD list of question bank |
| `POST` | `/api/questions/admin/mcq/` | Admin Only | Create MCQ question with answer options |
| `POST` | `/api/questions/admin/code/` | Admin Only | Create coding problem with test cases |
| `GET` | `/api/admin/analytics/export/?format=csv`| Admin Only | Stream institutional performance analytics as CSV |
| `GET` | `/api/health/` | Public | System and database operational health check |

*For complete request/response schemas and payload examples, refer to [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).*

---

## 6. Prerequisites & Installation Guide

### 6.1 Prerequisites
1. **Python 3.10+** (Python 3.10–3.14 verified)
2. **PostgreSQL 14+** (Service active on `localhost:5432`)
3. **Docker Engine & Docker Compose** (Required for Judge0 code execution)
4. **Git**

---

### 6.2 Step-by-Step Setup

#### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/your-org/skillbyte.git
cd skillbyte

# Create and activate Python virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

#### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configure PostgreSQL Database
Open your PostgreSQL shell (`psql`) or pgAdmin and run:
```sql
CREATE DATABASE skillbyte_db;
```

Create a `.env` file in the project root:
```ini
# Core Django Configuration
SECRET_KEY=skillbyte-insecure-development-secret-key-replace-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],testserver

# PostgreSQL Database Configuration (Strictly Required)
DB_NAME=skillbyte_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_HOST=localhost
DB_PORT=5432

# Judge0 Sandboxed Execution Microservice
JUDGE0_URL=http://localhost:2358

# JWT Parameters
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
```

#### Step 4: Apply Database Migrations & Seed Question Bank
```bash
cd backend

# Validate configuration
python manage.py check

# Apply PostgreSQL database migrations
python manage.py migrate

# Seed initial question bank with MCQs and Coding problems
python manage.py seed_questions
```

#### Step 5: Start Self-Hosted Judge0 Docker Stack
```bash
# In a separate terminal or Docker host
mkdir -p /opt/judge0 && cd /opt/judge0
curl -fsSL https://raw.githubusercontent.com/judge0/judge0/master/docker-compose.yml -o docker-compose.yml
curl -fsSL https://raw.githubusercontent.com/judge0/judge0/master/judge0.conf -o judge0.conf
docker compose up -d

# Verify health status
curl http://localhost:2358/system_info
```

#### Step 6: Create Administrative Accounts
```bash
# Interactive administrator creation
python manage.py setup_admin

# Or promote an existing registered user
python manage.py promote_admin --email admin@skillbyte.edu
```

#### Step 7: Launch Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open your browser and navigate to **`http://127.0.0.1:8000/`**.

---

## 7. Running the Automated Test Suite

SkillByte contains 68 automated unit and integration tests covering authentication, question bank management, assessment lifecycles, Judge0 integration, scoring deduplication, leaderboards, and administrative analytics:

```bash
cd backend

# Run the complete test suite (all 5 modules)
python manage.py test questions.tests_phase11 questions.tests_phase10 questions.tests_phase9 questions.tests accounts
```

### Verified Test Results:
```shell
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....................................................................
----------------------------------------------------------------------
Ran 68 tests in 75.260s

OK
Destroying test database for alias 'default'...
```

---

## 8. Chrome / CDP End-to-End Browser Verification

In addition to automated Python tests, 10 complete user journeys were verified using the Chrome DevTools Protocol (CDP) on an active local instance:

| # | User Scenario Verified | Target Route | Result | Console Errors |
|:---:|---|---|:---:|:---:|
| 1 | Student Profile Editing & Immediate Navbar Reflection | `/profile/` | **PASS** | 0 |
| 2 | Secure Password Change with Old Password Verification | `/profile/` | **PASS** | 0 |
| 3 | Responsive Navbar Toggle on Mobile Viewport (375px) | `/` | **PASS** | 0 |
| 4 | Active Assessment Detection & Resumption across Reload | `/coding/assessment/<id>/` | **PASS** | 0 |
| 5 | Explicit Assessment Abandonment with Modal Dialog | `/assessments/mcq/<id>/` | **PASS** | 0 |
| 6 | Solution Utilities: Copy Code, Download File, Practice Again | `/coding/result/<id>/` | **PASS** | 0 |
| 7 | Admin Analytics KPI Dashboard & One-Click CSV Export | `/admin/analytics/` | **PASS** | 0 |
| 8 | RBAC Enforcement (Student/Guest Blocked from Admin) | `/admin/questions/` | **PASS** | 0 |
| 9 | Custom Branded Error Templates (404, 403, 500) | `/invalid-route/` | **PASS** | 0 |
| 10 | JavaScript Console Error Monitoring across All Views | All Primary Pages | **PASS** | **0** |

---

## 9. Security & Sandboxing Highlights

- **PBKDF2 Password Hashing**: 600,000 SHA-256 iterations with unique cryptographic salt per user.
- **Stateless JWT Tokens**: Signed via HS256 with automatic rotation on refresh and immediate blacklisting on logout.
- **Zero-Leakage Data Sanitization**: Correct answer flags (`is_correct`) and hidden test cases (`is_hidden=True`) are strictly stripped by serializers before transmitting payloads to candidates.
- **Judge0 Container Hardening**: Untrusted student code runs inside throwaway Docker containers executed as unprivileged user `nobody` with 2.0s CPU limits, 256 MB memory caps, and completely disabled network interfaces (`--net none`).
- **Server-Authoritative Timing**: Timestamps are computed server-side (`started_at`); client-side JavaScript timer manipulation cannot grant extra exam time.
- **SQL & XSS Injection Protection**: 100% Django ORM parameterized queries; Django template auto-escaping; safe DOM handling.
- **DRF Rate Throttling**: 15 req/min on authentication, 30 req/min on code execution, 120 req/min on anonymous endpoints.

---

## 10. Future Scope & Roadmap

While SkillByte satisfies all requirements of the project SRS, future commercial and institutional enhancements include:
1. **Real-Time Multiplayer Coding Duels**: Integrating Django Channels (WebSockets) and Redis for live 1v1 competitive programming matches.
2. **Automated Plagiarism Detection**: Integrating an algorithmic code similarity engine (e.g., Stanford MOSS) to identify code duplication across candidates.
3. **AI-Assisted Debugging Hints**: Leveraging Large Language Models (LLMs) to generate dynamic, contextual hints for failing test cases without revealing solutions.
4. **Remote Exam Proctoring**: Client-side tab-switch detection, browser lock-down modes, and optional webcam-based presence monitoring.

---

## 11. Authors & Academic Acknowledgements

- **Students / Developers**: `[STUDENT_NAME_1]` (`[ROLL_NUMBER_1]`) & `[STUDENT_NAME_2]` (`[ROLL_NUMBER_2]`)
- **Internal Project Supervisor**: `[PROJECT_GUIDE_NAME]`, `[DESIGNATION_OF_GUIDE]`
- **Head of Department**: `[HOD_NAME]`, Department of `[DEPARTMENT_NAME]`
- **Institution**: `[COLLEGE_NAME]`, `[ACADEMIC_YEAR]`
- **License**: MIT License (for open academic and institutional use)
