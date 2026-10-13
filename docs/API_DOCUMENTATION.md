# SKILLBYTE — REST API Specification & Endpoint Catalog

> **Document ID**: `DELIV-03`  
> **Classification**: Production API Reference Specification  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Base URL**: `http://127.0.0.1:8000/api/`  
> **Protocol**: HTTP/1.1 REST with JSON Encodings  

---

## 1. Global API Standards & Protocols

### 1.1 Authentication & Request Headers
All protected endpoints require the HTTP `Authorization` header containing a valid JSON Web Token (JWT) formatted as:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```
For endpoints accessible to guests, sessions are tracked via the `X-Session-ID` header or auto-generated UUID cookies.

### 1.2 Rate Limiting (DRF Throttling)
To prevent denial-of-service, brute force, and sandbox resource exhaustion, the following rate limits are enforced via Django REST Framework:

| Scope | Rate Limit | Applied To |
|---|---|---|
| `anon` | **120 requests / minute** | Unauthenticated public endpoints |
| `user` | **1200 requests / minute** | Authenticated user sessions |
| `auth_attempt` | **15 requests / minute** | Login, registration, password change |
| `code_run` | **30 requests / minute** | Live coding execution (`/run/` and `/submit/`) |

### 1.3 Standard Error Responses
All error responses adhere to standard JSON error envelopes with explicit diagnostic details:
```json
{
  "detail": "Descriptive error message explaining the failure.",
  "code": "error_code_identifier"
}
```

---

## 2. API Endpoint Matrix (28 Endpoints)

| # | Method | Endpoint Route | Access / RBAC | Description |
|---|:---:|---|:---:|---|
| **1** | `POST` | `/api/auth/register/` | Public | Register a new student account |
| **2** | `POST` | `/api/auth/login/` | Public | Authenticate via email/username & obtain JWT tokens |
| **3** | `POST` | `/api/auth/token/refresh/` | Public | Refresh expired JWT access token |
| **4** | `POST` | `/api/auth/logout/` | Authenticated | Blacklist refresh token & terminate session |
| **5** | `GET/PUT/PATCH`| `/api/auth/me/` | Authenticated | Retrieve or update user profile and bio |
| **6** | `POST` | `/api/auth/change-password/` | Authenticated | Change user account password securely |
| **7** | `GET` | `/api/auth/test-student-role/` | Student Only | Verify student RBAC access control |
| **8** | `GET` | `/api/auth/test-admin-role/` | Admin Only | Verify administrator RBAC access control |
| **9** | `GET` | `/api/questions/` | Public / Student | List active questions with filtering |
| **10** | `GET` | `/api/questions/<id>/` | Public / Student | Retrieve sanitized details of a question |
| **11** | `GET` | `/api/assessments/active/` | Student / Guest | Detect active in-progress assessment attempt |
| **12** | `POST` | `/api/assessments/<id>/abandon/` | Student / Guest | Abandon an in-progress assessment |
| **13** | `POST` | `/api/assessments/mcq/start/` | Student / Guest | Initiate a new MCQ assessment session |
| **14** | `POST` | `/api/assessments/mcq/<id>/answer/`| Student / Guest | Record choice for an MCQ question |
| **15** | `POST` | `/api/assessments/mcq/<id>/submit/`| Student / Guest | Finalize MCQ assessment and compute score |
| **16** | `GET` | `/api/assessments/mcq/<id>/result/`| Student / Guest | View detailed MCQ assessment verdict |
| **17** | `POST` | `/api/assessments/coding/start/` | Student / Guest | Initiate a live coding assessment session |
| **18** | `GET` | `/api/assessments/coding/<id>/` | Student / Guest | Fetch coding problem details & starter code |
| **19** | `POST` | `/api/assessments/coding/<id>/run/` | Student / Guest | Run code against public sample test cases |
| **20** | `POST` | `/api/assessments/coding/<id>/submit/` | Student / Guest | Final submission evaluated against hidden tests |
| **21** | `GET` | `/api/assessments/coding/<id>/result/` | Student / Guest | Fetch coding submission verdict & failure tags |
| **22** | `GET` | `/api/assessments/my-attempts/` | Student / Guest | Retrieve historical assessment sessions |
| **23** | `GET` | `/api/assessments/progress/` | Student / Guest | Compute unified mastery score & skill tier |
| **24** | `GET` | `/api/leaderboard/` | Public / Student | Dynamic leaderboard with category & timeframe filters |
| **25** | `GET` | `/api/questions/admin/` | Admin Only | Full CRUD list of question bank |
| **26** | `POST` | `/api/questions/admin/mcq/` | Admin Only | Create MCQ with answer options |
| **27** | `POST` | `/api/questions/admin/code/` | Admin Only | Create coding problem with starter templates |
| **28** | `GET` | `/api/admin/analytics/export/?format=csv` | Admin Only | Stream platform analytics data as CSV |

---

## 3. Module-by-Module Detailed Endpoint Specification

---

### Module 3.1: Authentication & Profile APIs

#### 1. User Registration
- **Route**: `POST /api/auth/register/`
- **Permissions**: `AllowAny`
- **Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!"
}
```
- **Responses**:
  - `201 Created`:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 12,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "STUDENT"
  }
}
```
  - `400 Bad Request`: Validation failure (passwords do not match, email duplicate).

#### 2. User Login
- **Route**: `POST /api/auth/login/`
- **Permissions**: `AllowAny`
- **Request Body**: Accepts either username or email in the `username` field.
```json
{
  "username": "john@example.com",
  "password": "SecurePassword123!"
}
```
- **Responses**:
  - `200 OK`:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsIn...",
  "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
  "user": {
    "id": 12,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "STUDENT",
    "bio": ""
  }
}
```
  - `401 Unauthorized`: Invalid credentials.

#### 3. Token Refresh
- **Route**: `POST /api/auth/token/refresh/` (Alias: `/api/auth/refresh/`)
- **Permissions**: `AllowAny`
- **Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Response**: `200 OK` with a new `access` token and rotated `refresh` token.

#### 4. User Logout
- **Route**: `POST /api/auth/logout/`
- **Permissions**: `IsAuthenticated`
- **Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Response**: `200 OK` (`{"message": "Logged out successfully"}`). Refresh token is permanently blacklisted.

#### 5. Current User Profile
- **Route**: `GET/PUT/PATCH /api/auth/me/`
- **Permissions**: `IsAuthenticated`
- **PATCH Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Passionate Python developer preparing for interviews."
}
```
- **Response `200 OK`**: Updated user profile object with username, email, full name, role, and bio.

#### 6. Change Password
- **Route**: `POST /api/auth/change-password/`
- **Permissions**: `IsAuthenticated`
- **Request Body**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!",
  "confirm_password": "NewSecurePassword456!"
}
```
- **Response**: `200 OK` (`{"detail": "Password updated successfully."}`).

---

### Module 3.2: Question Catalog APIs

#### 7. Question List
- **Route**: `GET /api/questions/`
- **Permissions**: `AllowAny`
- **Query Parameters**:
  - `type`: `MCQ` or `CODE`
  - `category`: `Python`, `Java`, `Mathematics`, etc.
  - `difficulty`: `EASY`, `MEDIUM`, `HARD`
- **Response `200 OK`**:
```json
[
  {
    "id": 1,
    "title": "Two Sum Problem",
    "question_type": "CODE",
    "category": "Python",
    "difficulty": "EASY",
    "marks": 10,
    "time_limit": 2
  }
]
```

#### 8. Question Detail (Sanitized)
- **Route**: `GET /api/questions/<id>/`
- **Permissions**: `AllowAny`
- **Security Sanitization**: For MCQs, `options` are returned **without** `is_correct`. For Coding problems, test cases only include public sample cases (`is_hidden=False`).

---

### Module 3.3: Assessment Lifecycle & MCQ APIs

#### 9. Active Incomplete Assessment Check
- **Route**: `GET /api/assessments/active/`
- **Permissions**: `AllowAny` (Authenticated user or Guest via `session_id`)
- **Response `200 OK`**:
```json
{
  "has_active": true,
  "attempt": {
    "id": 104,
    "question_type": "CODE",
    "category": "Python",
    "time_limit_seconds": 600,
    "time_remaining_seconds": 452,
    "resume_url": "/coding/assessment/104/"
  }
}
```

#### 10. Abandon Assessment
- **Route**: `POST /api/assessments/<id>/abandon/`
- **Permissions**: Session Owner (Student or Guest)
- **Response `200 OK`**:
```json
{
  "message": "Assessment marked as abandoned",
  "status": "ABANDONED"
}
```

#### 11. Start MCQ Assessment
- **Route**: `POST /api/assessments/mcq/start/`
- **Request Body**:
```json
{
  "category": "Mathematics",
  "difficulty": "EASY",
  "time_limit_seconds": 300
}
```
- **Response `201 Created`**: Returns generated `attempt_id` and list of questions with answer choices (`is_correct` stripped).

#### 12. Submit MCQ Assessment
- **Route**: `POST /api/assessments/mcq/<id>/submit/`
- **Response `200 OK`**:
```json
{
  "attempt_id": 104,
  "status": "COMPLETED",
  "total_score": 8.0,
  "max_score": 10,
  "percentage": 80.0,
  "breakdown": [
    {
      "question_id": 15,
      "selected_option": "B",
      "correct_option": "B",
      "is_correct": true,
      "marks": 1.0,
      "explanation": "Derived using the quadratic theorem."
    }
  ]
}
```

---

### Module 3.4: Live Coding Execution APIs

#### 13. Run Code (Sample Test Cases)
- **Route**: `POST /api/assessments/coding/<attempt_id>/run/`
- **Rate Limit**: `code_run: 30/minute`
- **Request Body**:
```json
{
  "language": "python",
  "source_code": "def solution(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i"
}
```
- **Response `200 OK`**:
```json
{
  "overall_status": "ACCEPTED",
  "passed_test_cases": 2,
  "total_test_cases": 2,
  "results": [
    {
      "test_case_id": 1,
      "stdin": "[2, 7, 11, 15]\n9",
      "expected_output": "[0, 1]",
      "actual_output": "[0, 1]",
      "status": "ACCEPTED",
      "execution_time": 0.03,
      "memory_kb": 8420
    }
  ]
}
```

#### 14. Submit Coding Solution (Hidden Test Cases & Grading)
- **Route**: `POST /api/assessments/coding/<attempt_id>/submit/`
- **Request Body**: Same schema as `/run/`.
- **Backend Execution Flow**:
  1. Queries all test cases (both public sample and hidden).
  2. Dispatches individual runs to Judge0 sandbox.
  3. Validates stdout against expected output.
  4. Tags failures: `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `WRONG_ANSWER`, or `ACCEPTED`.
  5. Computes partial credit: $\text{score} = \left(\frac{\text{passed\_test\_cases}}{\text{total\_test\_cases}}\right) \times \text{question.marks}$.
  6. Locks attempt as `COMPLETED`.
- **Response `200 OK`**:
```json
{
  "submission_id": 482,
  "status": "ACCEPTED",
  "score": 10.0,
  "passed_test_cases": 5,
  "total_test_cases": 5,
  "execution_time": 0.04,
  "memory_usage": 9120.0,
  "message": "Submission evaluated successfully."
}
```

---

### Module 3.5: Student Progress & Gamification APIs

#### 15. Student Progress & Mastery
- **Route**: `GET /api/assessments/progress/` (Alias: `/api/assessments/my-progress/`)
- **Response `200 OK`**:
```json
{
  "total_points": 185.0,
  "skill_tier": "Specialist",
  "badge_class": "bg-warning text-dark",
  "theory_points": 65.0,
  "practice_points": 120.0,
  "category_mastery": {
    "Python": {"points": 80.0, "solved": 8},
    "Mathematics": {"points": 45.0, "solved": 15},
    "DSA": {"points": 40.0, "solved": 4}
  }
}
```

#### 16. Dynamic Leaderboard
- **Route**: `GET /api/leaderboard/`
- **Query Parameters**:
  - `timeframe`: `all_time` (default), `month`, `week`
  - `category`: `all` (default), or specific subject (`Python`, `Java`, etc.)
- **Response `200 OK`**:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": 5,
      "username": "alex_coder",
      "total_score": 340.0,
      "theory_score": 90.0,
      "practice_score": 250.0,
      "skill_tier": "Master",
      "tier_class": "bg-danger"
    },
    {
      "rank": 2,
      "user_id": 12,
      "username": "johndoe",
      "total_score": 185.0,
      "theory_score": 65.0,
      "practice_score": 120.0,
      "skill_tier": "Specialist",
      "tier_class": "bg-warning text-dark"
    }
  ]
}
```

---

### Module 3.6: Admin Management & Analytics Export APIs

#### 17. Admin Analytics Export (CSV)
- **Route**: `GET /api/admin/analytics/export/?format=csv`
- **Permissions**: `IsAdminUser` (`role=ADMIN` or `is_staff=True`)
- **Response Headers**:
```http
Content-Type: text/csv
Content-Disposition: attachment; filename="skillbyte_analytics_summary.csv"
```
- **Response Body**:
```csv
Metric,Value
Total Registered Users,42
Total Attempts,315
Completed Attempts,280
Completion Rate,88.89%
Average MCQ Score,7.4 / 10
Average Coding Score,8.1 / 10
```

#### 18. System Health Check
- **Route**: `GET /api/health/`
- **Permissions**: `AllowAny`
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "judge0": "reachable",
  "timestamp": "2026-09-23T18:30:00Z"
}
```

