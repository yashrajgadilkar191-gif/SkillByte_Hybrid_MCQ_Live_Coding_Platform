# SKILLBYTE — "Where Theory Meets Practice"

SKILLBYTE is a college Mini Project designed as a comprehensive hybrid assessment platform that unifies:
1. **MCQ-Based Theoretical Assessment** (General Knowledge, English, Mathematics)
2. **Live Coding Assessment** (Python, Java, C++, DSA via Monaco Editor & Judge0)

---

## 1. Project Purpose

SkillByte bridges the gap between theoretical knowledge and practical coding ability. Students and candidates practice multiple-choice assessments and real-time coding problems from a single, unified interface, with unified progress tracking, leaderboard rankings, and performance analytics.

---

## 2. Technology Stack

- **Backend Framework**: Python 3.14, Django 5.2, Django REST Framework (DRF)
- **Database**: PostgreSQL (exclusively using Django ORM; no SQLite fallback)
- **Authentication**: JWT (`djangorestframework-simplejwt` with Token Blacklisting) + Django Auth
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6+), Bootstrap 5.3, Monaco Editor (CDN)
- **Code Execution**: Judge0 API (official remote execution engine)
- **Architecture**: Modular Django monolithic architecture serving REST APIs and responsive UI

---

## 3. Project Structure

```
MiniProject/
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration (git-ignored)
├── .gitignore                # Git exclusions
├── requirements.txt          # Python dependencies
├── manage.py                 # Root management convenience wrapper
├── README.md                 # Project documentation
│
├── backend/                  # Django project root
│   ├── manage.py             # Django management CLI
│   ├── config/               # Project configuration package
│   │   ├── __init__.py
│   │   ├── settings.py       # PostgreSQL-only settings, DRF, CORS, SimpleJWT
│   │   ├── urls.py           # Core routing (admin, api/auth, api, frontend pages)
│   │   ├── wsgi.py           # WSGI entrypoint
│   │   └── asgi.py           # ASGI entrypoint
│   ├── accounts/             # Authentication & User Role Management (Phase 2)
│   │   ├── __init__.py
│   │   ├── admin.py          # Django Admin User & Profile integration
│   │   ├── apps.py           # AppConfig & signals registration
│   │   ├── backends.py       # Case-insensitive email authentication backend
│   │   ├── models.py         # UserProfile (OneToOne with User, Role choices)
│   │   ├── permissions.py    # Reusable RBAC permissions (IsStudent, IsAdmin)
│   │   ├── serializers.py    # Register, Login, User, Logout serializers
│   │   ├── signals.py        # Automatic UserProfile creation signal
│   │   ├── tests.py          # 14 automated unit tests for auth & RBAC
│   │   ├── urls.py           # /api/auth/ endpoints
│   │   ├── views.py          # Register, Login, Me, Logout, Role tests
│   │   └── management/
│   │       └── commands/
│   │           ├── setup_admin.py    # Secure admin creation CLI
│   │           └── promote_admin.py  # User promotion CLI
│   └── api/                  # Core API app
│       ├── __init__.py
│       ├── apps.py
│       ├── tests.py          # Health check and frontend view tests
│       ├── urls.py           # /api/health/ routing
│       └── views.py          # health_check & frontend page views
│
└── frontend/                 # Frontend assets & templates
    ├── templates/
    │   ├── base.html         # Base HTML5 layout with Bootstrap 5 & navbar
    │   ├── index.html        # Landing page with dynamic status & CTAs
    │   ├── login.html        # Student/Admin login page
    │   ├── register.html     # Student registration page (strictly no admin role)
    │   └── dashboard.html    # Dashboard foundation with role inspection
    └── static/
        ├── css/
        │   └── main.css      # Core theme styles, variables, card styles
        └── js/
            ├── main.js       # Asynchronous API health status checker
            └── auth.js       # Client JWT session manager & auth state
```

---

## 4. Prerequisites

1. **Python 3.10+** (Python 3.14 verified)
2. **PostgreSQL 14+** (PostgreSQL 18 service running on `localhost:5432`)
3. **pip** (Python package manager)

---

## 5. PostgreSQL Setup & Configuration

SkillByte is strictly configured to use PostgreSQL. No SQLite fallback is permitted.

### Step 1: Create Database
Open your PostgreSQL terminal (`psql`) or pgAdmin and run:
```sql
CREATE DATABASE skillbyte_db;
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` (if not already present):
```bash
cp .env.example .env
```

Open `.env` and fill in your PostgreSQL credentials:
```env
# Django Settings
SECRET_KEY=your_secure_random_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],testserver

# PostgreSQL Database Configuration (Required)
DB_NAME=skillbyte_db
DB_USER=postgres
DB_PASSWORD=your_actual_postgres_password
DB_HOST=localhost
DB_PORT=5432

# SimpleJWT Configuration (Optional overrides)
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
```

---

## 6. Installation & Execution Commands

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Check Django Configuration
```bash
python manage.py check
```

### Step 3: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Seed Question Bank (Phase 3)
```bash
python manage.py seed_questions
```

### Step 5: Run Automated Tests
```bash
python manage.py test accounts questions api
```

### Step 6: Start Development Server
```bash
python manage.py runserver
```
The application will be accessible at `http://127.0.0.1:8000/`.

---

## 7. Authentication & Role Management (Phase 2)

### 7.1 Architecture & User Model Decision
To maintain clean database integrity with Django's existing authentication tables, we use a clean `OneToOne` `UserProfile` model linked to Django's standard `User` model:
- Utilizes Django's battle-tested PBKDF2 password hashing.
- Supports case-insensitive email-based authentication via `accounts.backends.EmailOrUsernameBackend`.
- Automatic profile creation and synchronization handled via `post_save` signals in `accounts/signals.py`.
- Roles supported: `STUDENT`, `ADMIN`, `GUEST`.

### 7.2 User Roles & Access Policy
1. **STUDENT**:
   - Registered through public signup (`POST /api/auth/register/`).
   - Can log in, obtain JWT access/refresh tokens, and access student features.
2. **ADMIN**:
   - **Never selectable during public registration.** Attempts to submit `role: ADMIN` are strictly rejected.
   - Created or promoted exclusively through secure server-side management commands.
   - Has full access to Django admin and upcoming admin question/analytics management.
3. **GUEST**:
   - Allows prospective students to explore the platform without permanent score storage.
   - Managed client-side and authenticated via temporary guest state.

### 7.3 Admin Setup & Promotion Commands

#### Create a New Administrator Account:
```bash
# Interactive mode (prompts for username, email, full name, and password securely):
python manage.py setup_admin

# Non-interactive mode (e.g. for deployment/scripting):
python manage.py setup_admin --username admin --email admin@skillbyte.edu --name "System Administrator" --password "SecureAdminPassword123"
```

#### Promote an Existing Student to Administrator:
```bash
python manage.py promote_admin --email student@skillbyte.edu
```

---

## 8. Question Bank & Assessments Foundation (Phase 3)

### 8.1 Core Models & Schema Design
- **`Question`**: Unified model supporting both `MCQ` and `CODE` assessment items.
  - Categories:
    - **MCQ Subjects**: `General Knowledge`, `English`, `Mathematics`
    - **Coding Categories**: `Python`, `Java`, `C++`, `DSA`
  - Difficulties: `EASY`, `MEDIUM`, `HARD`
  - Resource Limits: `time_limit` (seconds), `memory_limit` (MB).
  - Coding Specs: `input_format`, `output_format`, `constraints`, `sample_input`, `sample_output`, `starter_code` (JSON dictionary for language templates).
- **`QuestionOption`**: Options for MCQ questions. Foreign key to `Question`.
  - Stores `option_key` (A, B, C, D), `option_text`, and `is_correct`.
  - **Security Rule**: `is_correct` is strictly omitted from student serializers.
- **`TestCase`**: Test suites for Coding problems. Foreign key to `Question`.
  - Stores `input_data`, `expected_output`, `is_hidden`, `marks`, `time_limit`, `memory_limit`.
  - **Security Rule**: Hidden test cases (`is_hidden=True`) and their expected outputs are strictly excluded from student APIs.
- **`AssessmentAttempt`**: Assessment sessions initiated by students or guests.
  - Supports guest attempts (`user=None`, `session_id` populated) and registered student attempts (`user=User`).
  - Statuses: `IN_PROGRESS`, `COMPLETED`, `ABANDONED`.
- **`MCQAnswer`**: Records chosen options, correctness, and marks per question attempt.
- **`CodingSubmission`**: Foundation for code submissions; tracks `language`, `source_code`, `status` (`ACCEPTED`, `PARTIAL`, `WRONG_ANSWER`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `SERVICE_UNAVAILABLE`, `PENDING`), `score`, `passed_test_cases`, `execution_time`, `memory_usage`, and `error_output`.
- **`AssessmentResult`**: One-to-one summary result linked to `AssessmentAttempt`, calculating `obtained_marks`, `total_marks`, and `percentage`.

### 8.2 Database Seeding Command
A safe development command populates initial questions with options and test cases:
```bash
python manage.py seed_questions
```

---

## 9. MCQ Assessment Engine (Phase 4)

### 9.1 Assessment Lifecycle & Architecture
1. **Selection & Initiation (`POST /api/assessments/mcq/start/`)**:
   - Students or Guests configure `category` (General Knowledge, English, Mathematics), `difficulty` (EASY, MEDIUM, HARD), and `question_count`.
   - The server queries active questions, performs safe randomization (`.order_by('?')`), calculates total score and duration, and instantiates an `AssessmentAttempt` with status `IN_PROGRESS`.
   - Questions are returned with sanitized options (**`is_correct` is strictly omitted**).
2. **Real-Time Authoritative Timer**:
   - The server records `started_at` and `time_limit_seconds`. The frontend display is merely visual.
   - When time expires, server-side checks reject further answers and automatically execute evaluation.
3. **Interactive Answer Submission (`POST /api/assessments/mcq/<id>/answer/`)**:
   - Submits `question_id` and `option_id`.
   - Validates that the question belongs to this specific attempt and the option belongs to the question.
   - Updates `MCQAnswer` records. Final marks are NOT calculated or exposed on the client.
4. **Server-Side Scoring & Submission (`POST /api/assessments/mcq/<id>/submit/`)**:
   - Evaluates each answer against `QuestionOption.is_correct`.
   - Allocates `question.marks` for correct answers and 0 for incorrect or unanswered questions.
   - Computes `obtained_marks`, `total_marks`, `percentage`, `correct_answers`, `wrong_answers`, and `unanswered`.
   - Marks attempt as `COMPLETED` and records an immutable `AssessmentResult`.
   - Double submissions and answering completed attempts are strictly prevented.
5. **Results & Question Review (`GET /api/assessments/mcq/<id>/result/`)**:
   - Provides score breakdown and review cards showing chosen options, correct answers, and detailed explanations.
6. **Student History (`GET /api/assessments/my-attempts/`)**:
   - Authenticated students can review their past assessment attempts. Strictly isolated so students only see their own attempts.
7. **Guest Flow vs. Student Flow**:
   - **Guests**: `user=None`. Secured via an automated `session_id` generated at start. Results are displayed but not permanently associated with student leaderboards.
   - **Students**: Authenticated via JWT Bearer token. Attempts are permanently stored and linked to `request.user`.

---

---

## 10. Live Coding Assessment Module (Phase 5)

### 10.1 Live Coding Architecture & Workflow
1. **Problem Directory & Setup (`/coding/`, `/coding/setup/`)**:
   - Students and Guests can browse coding problems across **Python**, **Java**, **C++**, and **DSA**.
   - Filter by programming category and difficulty level (`EASY`, `MEDIUM`, `HARD`), or configure custom assessment time limits (15, 30, 45, 60 minutes).
2. **Monaco Editor Workspace (`/coding/assessment/<attempt_id>/`)**:
   - Integrated full-featured code editor loaded securely from CDN (`https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/`).
   - Theme: `vs-dark`, JetBrains Mono typography, syntax highlighting, line numbers, automatic layout, and minimap.
   - Dynamic language switching (Python, Java, C++) with confirmation modals preventing accidental code loss.
   - Language-specific starter code templates loaded directly from the database question model.
3. **Strict Security & Zero Information Leakage**:
   - **Hidden Testcases Protected**: `is_hidden=True` test cases and their expected outputs are strictly filtered out by the serializer and never sent over the network.
   - Only sample, public test cases are provided for candidate guidance.
4. **Honest Execution Model & Judge0 Readiness**:
   - **No Arbitrary Local Code Execution**: To ensure absolute server safety, no arbitrary code is ever executed directly on the host machine using `subprocess` or `os.system`.
   - **Informative "Run Code" Modal**: The "Run Code" button explicitly notifies the candidate that remote automated judging is scheduled for Phase 6 Judge0 integration. No fake or fabricated verdicts are generated.
5. **Server-Authoritative Timer & PENDING Submissions**:
   - The countdown timer is tracked server-side (`started_at + time_limit_seconds`).
   - Submissions sent to `POST /api/assessments/coding/<attempt_id>/submit/` are persisted to PostgreSQL in the `CodingSubmission` model with status `PENDING`.
   - The attempt transitions to `COMPLETED`, recording timestamp and language for evaluation in Phase 6.
6. **Submission Result Page (`/coding/result/<attempt_id>/`)**:
   - Provides a comprehensive submission summary, selected language, time taken, submitted source code view, and clear `PENDING` status badge.

---

## 11. REST API Endpoints

### Core & Health
| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `GET` | `/api/health/` | Public | System and DRF operational health status |

### Authentication (Phase 2)
| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `POST` | `/api/auth/register/` | Public | Register new student account (enforces `STUDENT` role) |
| `POST` | `/api/auth/login/` | Public | Email/password login; returns JWT `access` & `refresh` |
| `POST` | `/api/auth/token/refresh/` | Public | Exchanges valid refresh token for a new access token |
| `POST` | `/api/auth/logout/` | Authenticated | Blacklists the refresh token and terminates the session |
| `GET` | `/api/auth/me/` | Authenticated | Returns currently authenticated user details (`id`, `name`, `email`, `role`) |
| `GET` | `/api/auth/test-student-role/` | Student Only | Verified endpoint testing `IsStudent` permission (403 for non-students) |
| `GET` | `/api/auth/test-admin-role/` | Admin Only | Verified endpoint testing `IsAdmin` permission (403 for students) |

### Question Bank (Phase 3)
| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `GET` | `/api/questions/` | Public / Student | List active questions with filters (`type`, `category`, `difficulty`) |
| `GET` | `/api/questions/<id>/` | Public / Student | Sanitized question detail (omits `is_correct` & hidden test cases) |

### MCQ Assessment Engine (Phase 4)
| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `POST` | `/api/assessments/mcq/start/` | Public / Guest / Student | Start MCQ assessment session; returns attempt metadata & questions |
| `POST` | `/api/assessments/mcq/<id>/answer/` | Attempt Owner | Record option selection for a question in an in-progress attempt |
| `POST` | `/api/assessments/mcq/<id>/submit/` | Attempt Owner | Submit assessment, calculate official score, and produce result |
| `GET` | `/api/assessments/mcq/<id>/result/` | Attempt Owner | View score summary and question-by-question review with explanations |
| `GET` | `/api/assessments/my-attempts/` | Authenticated Student | List authenticated student's previous assessment attempts (MCQ + Code) |

### Live Coding Assessment (Phase 5)
| Method | Endpoint | Access | Description |
|:---|:---|:---|:---|
| `POST` | `/api/assessments/coding/start/` | Public / Guest / Student | Start live coding assessment session; returns sanitized problem and starter code |
| `GET` | `/api/assessments/coding/<id>/` | Attempt Owner | Workspace state, remaining timer seconds, problem details, and saved code |
| `POST` | `/api/assessments/coding/<id>/submit/` | Attempt Owner | Submit code solution; creates `CodingSubmission` with `PENDING` status |
| `GET` | `/api/assessments/coding/<id>/result/` | Attempt Owner | View submitted code, language, time taken, and pending evaluation state |

---

## 12. Security Notes

- **Password Hashing**: Django's PBKDF2 with SHA-256 algorithm. Passwords are never returned in any API response or logged.
- **JWT Protection**: Tokens signed with project `SECRET_KEY` loaded from environment variables.
- **Token Blacklisting**: Logout immediately blacklists the refresh token in PostgreSQL via `rest_framework_simplejwt.token_blacklist`. Subsequent refresh requests with the blacklisted token are rejected with HTTP 401.
- **Role Elevation Defense**: Serializer-level and view-level guards prevent clients from injecting or claiming the `ADMIN` role.
- **Sanitized Assessment Data**: Student-facing serializers strictly exclude `is_correct` flags on MCQ options and hidden test cases (`is_hidden=True`) on coding problems.
- **Zero Arbitrary Execution**: Server never invokes local compilers or `subprocess` commands on submitted student code. Code execution is strictly scheduled for isolated Judge0 remote sandboxing in Phase 6.
- **Server-Side Scoring**: Clients can never submit scores or marks. Scoring is exclusively computed against database ground-truth upon submission.
- **Ownership Isolation**: Cross-student and cross-guest access to attempts is strictly forbidden (HTTP 403).
- **Database Safety**: 100% Django ORM queries; no raw SQL; exclusive PostgreSQL configuration.

