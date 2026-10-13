# SKILLBYTE — Security Architecture & Threat Modeling Manual

> **Document ID**: `DELIV-05`  
> **Classification**: Security Architecture & Defensive Specification  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Standard Compliance**: OWASP Top 10 (2021), STRIDE Threat Modeling  

---

## 1. Core Security Architecture & Defensive Philosophy

SkillByte adopts a **Defense-in-Depth** and **Zero Client Trust** architectural philosophy. Because online coding assessment platforms execute arbitrary, untrusted source code provided by remote candidates, strict isolation, input sanitization, and cryptographic identity boundaries are enforced at every tier.

```
+-------------------------------------------------------------------------+
| Layer 1: Network & Rate Limiting                                        |
| - DRF Scoped Rate Throttling (15/min auth, 30/min code run, 120/min anon)|
| - CORS Allowed Origins Whitelist                                        |
+------------------------------------+------------------------------------+
                                     v
+-------------------------------------------------------------------------+
| Layer 2: Authentication & Session Protection                            |
| - PBKDF2 Password Hashing (SHA-256, 600,000 iterations)                 |
| - Stateless JWT with Rotation & Blacklisting (SimpleJWT)                |
+------------------------------------+------------------------------------+
                                     v
+-------------------------------------------------------------------------+
| Layer 3: Role-Based Authorization & Data Sanitization                   |
| - Granular RBAC: Admin > Student > Guest                                |
| - Zero-Leakage: is_correct and is_hidden fields stripped server-side    |
+------------------------------------+------------------------------------+
                                     v
+-------------------------------------------------------------------------+
| Layer 4: Sandboxed Code Execution                                       |
| - Self-Hosted Judge0 in Docker Containers                               |
| - Dropped root privileges (runs as 'nobody' user)                       |
| - Linux cgroups: 2.0s CPU time limit, 256MB RAM ceiling                 |
| - Severed egress networking (No internet/socket access)                 |
+-------------------------------------------------------------------------+
```

---

## 2. Authentication & Credential Security

### 2.1 Password Hashing & Salt Security
All passwords stored in the PostgreSQL `auth_user` table are hashed using Django’s battle-tested PBKDF2 (Password-Based Key Derivation Function 2) implementation:
- **Algorithm**: `PBKDF2-HMAC-SHA256`
- **Work Factor**: 600,000 iterations (OWASP recommended standard)
- **Salt Generation**: 128-bit cryptographically secure random salt generated via `os.urandom()` per user
- **Storage Format**: `pbkdf2_sha256$600000$<salt>$<hash>`

### 2.2 Stateless JWT Token Lifecycle & Rotation
API authentication relies on the JSON Web Token (JWT) standard implemented via `djangorestframework-simplejwt`:
- **Algorithm**: `HS256` signed using the server's `SECRET_KEY`
- **Access Token Lifetime**: 60 minutes (`JWT_ACCESS_MINUTES=60`)
- **Refresh Token Lifetime**: 7 days (`JWT_REFRESH_DAYS=7`)
- **Automatic Token Rotation**: Each time a client calls `/api/auth/token/refresh/`, a new access token AND a new rotated refresh token are issued (`ROTATE_REFRESH_TOKENS = True`).
- **Token Blacklisting**: The prior refresh token is automatically stored in the database blacklist table (`BLACKLIST_AFTER_ROTATION = True`), preventing replay attacks and token harvesting.
- **Explicit Logout**: When `/api/auth/logout/` is called, the current refresh token is instantly blacklisted.

---

## 3. Role-Based Access Control (RBAC) Hierarchy

SkillByte enforces a three-tier hierarchical RBAC model:

```
[ADMIN] (Superuser / Staff)
  ├── Full Question Bank CRUD (Create, Read, Update, Delete)
  ├── Hidden Test Case Management
  ├── Platform-Wide Analytics & Metrics
  └── CSV Data Export Access
  │
[STUDENT] (Registered & Authenticated)
  ├── Personalized Dashboard & Skill Tier Progression
  ├── Attempt MCQ & Coding Assessments
  ├── View Personal Attempt History & Mastery Metrics
  ├── Profile Editing & Password Change
  └── View Leaderboard Rankings
  │
[GUEST] (Anonymous with Session UUID)
  ├── Practice MCQ & Coding Assessments in Sandboxed Mode
  ├── View Public Question Catalog
  ├── Temporary Session-Based Attempt Review
  └── Blocked from Leaderboard, Profile, & Persistent History
```

### 3.1 Permission Enforcement at View Level
Enforced via DRF permission classes (`accounts/permissions.py`):
```python
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser or 
             (hasattr(request.user, 'profile') and request.user.profile.is_admin))
        )
```
- Administrative views (`/api/questions/admin/`, `/api/admin/analytics/`) reject unauthorized students with `HTTP 403 Forbidden`.
- Assessment modification endpoints verify object-level ownership: students can only abandon or submit attempts where `attempt.user == request.user`.

---

## 4. Zero-Leakage Data Sanitization

A critical vulnerability in educational assessment software is the premature exposure of solutions via network traffic inspection (DevTools Network tab). SkillByte implements **Zero-Leakage Data Sanitization** in the serialization layer:

### 4.1 MCQ Answer Key Sanitization
When questions are retrieved during an active assessment, `QuestionOptionSerializer` unconditionally omits the `is_correct` field:
```python
class QuestionOptionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_key', 'option_text']  # 'is_correct' is strictly omitted
```
The correct answer is only revealed inside `MCQAssessmentSubmitView` after the assessment status transitions to `COMPLETED`.

### 4.2 Hidden Test Case Sanitization
During coding practice and active coding assessments, students have access only to public sample test cases:
```python
class QuestionSanitizedSerializer(serializers.ModelSerializer):
    test_cases = serializers.SerializerMethodField()

    def get_test_cases(self, obj):
        # Excludes all hidden test cases from student payloads
        public_cases = obj.test_cases.filter(is_hidden=False)
        return TestCasePublicSerializer(public_cases, many=True).data
```
Grading against `is_hidden=True` test cases is executed entirely server-side inside `CodingAssessmentSubmitView`.

---

## 5. Sandboxed Code Execution Isolation (Judge0)

Executing arbitrary user-submitted Python, Java, or C++ code creates severe attack surfaces. SkillByte neutralizes these threats by delegating execution to a self-hosted **Judge0** instance operating within Docker containers.

```
Host Operating System (Windows / Linux)
   └── Docker Engine
         └── Judge0 Worker Container
               └── Ephemeral Execution Container (Spawned per test case)
                     ├── User: 'nobody' (UID: 65534, GID: 65534)
                     ├── cgroups: CPU limit 2.0s, RAM limit 256MB
                     ├── File System: Read-only root, ephemeral tmpfs
                     └── Networking: Completely disabled (--net none)
```

### 5.1 Defensive Isolation Controls

| Threat / Attack Vector | Exploit Payload Example | Judge0 / SkillByte Defensive Mitigation |
|---|---|---|
| **Host System Compromise** | `import os; os.system('rm -rf /')` | Execution runs as unprivileged user `nobody` inside a throwaway container; root filesystem is read-only. |
| **Denial of Service (CPU)** | `while True: pass` | Linux cgroups enforce hard CPU time limit (2.0s); worker process is terminated via `SIGKILL`; status `TIME_LIMIT_EXCEEDED` returned. |
| **Denial of Service (RAM)** | `x = [0] * (10**9)` | Linux cgroups enforce 256 MB memory ceiling; process terminated via `SIGKILL` (OOM Killer); status `RUNTIME_ERROR` returned. |
| **Fork Bomb Attack** | `import os; [os.fork() for _ in range(100)]` | Process count limit (`pids_limit: 64`) prevents runaway process creation; child processes fail to fork. |
| **Network Data Exfiltration / SSRF** | `import urllib.request; urllib.request.urlopen(...)` | Execution container is launched with `--net none`; socket creation and outbound DNS/TCP requests fail immediately. |
| **Disk Space Exhaustion** | `with open('huge.txt', 'w') as f: f.write('0'*10**9)` | Ephemeral `tmpfs` mounts with strict maximum file size quotas (default 10 MB); file writes beyond limit trigger `SIGXFSZ`. |

---

## 6. Rate Limiting & Denial-of-Service Protection

Configured in `backend/config/settings.py` via DRF Throttling:
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/minute',
        'user': '1200/minute',
        'auth_attempt': '15/minute',
        'code_run': '30/minute',
    }
}
```
- Requests exceeding these thresholds receive `HTTP 429 Too Many Requests` with a `Retry-After` header.

---

## 7. STRIDE Threat Model Assessment

| Threat Category | Description in SkillByte Context | Mitigation Strategy & Verification |
|---|---|---|
| **Spoofing** | Attacker attempts to impersonate another student on the leaderboard. | Stateless HS256 JWT tokens signed with server `SECRET_KEY`; user identity extracted directly from verified token claims. |
| **Tampering** | Student alters client JavaScript to award themselves full marks or extend the timer. | Zero client trust. Assessment score computation and timer verification (`now() - started_at <= time_limit`) are executed strictly on the server. |
| **Repudiation** | Candidate claims an assessment was submitted without their knowledge. | Every attempt links to `user_id`, timestamps, and IP telemetry; status transitions from `IN_PROGRESS` to `COMPLETED` are recorded immutably. |
| **Information Disclosure** | Candidate inspects network traffic to see hidden test cases or MCQ answer keys. | Zero-leakage data sanitization; serializers filter out `is_correct` and `is_hidden=True` test cases. |
| **Denial of Service** | Malicious bot spams code execution requests to exhaust Judge0 workers. | DRF scoped rate limiters (`code_run: 30/minute`); Judge0 submission queue manages execution concurrency. |
| **Elevation of Privilege** | Student calls admin endpoints to create questions or export analytics. | View-level RBAC classes (`IsAdminUser`) check database role before dispatching controller logic. |

---

## 8. OWASP Top 10 (2021) Compliance Matrix

| OWASP Vulnerability | Risk Level | SkillByte Defensive Implementation |
|---|:---:|---|
| **A01: Broken Access Control** | High | Role-based permission classes on all administrative and user-isolated routes. |
| **A02: Cryptographic Failures** | High | PBKDF2 password hashing (600,000 iterations); HS256 JWT signing; HTTPS enforcement in production. |
| **A03: Injection (SQL / Command)** | Critical | Django ORM parameterized queries eliminate SQL injection; Judge0 containerization eliminates host command injection. |
| **A04: Insecure Design** | Medium | Server-authoritative timer and deduplicated scoring model designed into the architecture from Phase 1. |
| **A05: Security Misconfiguration** | Medium | Custom 404, 403, and 500 error views prevent Django debug stacktrace disclosure in production; strict CORS allowed origins. |
| **A06: Vulnerable & Outdated Components** | Medium | Modern, LTS component versions (Python 3.10+, Django 4.2+, PostgreSQL 15+). |
| **A07: Identification & Authentication Failures** | High | Token rotation, token blacklisting upon logout, and brute-force throttling on auth endpoints. |
| **A08: Software & Data Integrity Failures** | Medium | Transactional database integrity wrappers (`transaction.atomic`) prevent partial state commits. |
| **A09: Security Logging & Monitoring Failures** | Low | Consolidated application logging for assessment attempts and code submissions. |
| **A10: Server-Side Request Forgery (SSRF)** | High | Judge0 containers operate with zero network interfaces (`--net none`), preventing internal intranet scanning. |

