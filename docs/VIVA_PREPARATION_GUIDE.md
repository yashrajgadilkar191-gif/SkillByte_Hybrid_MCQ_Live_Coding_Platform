# SKILLBYTE — Viva Voce & Technical Defense Preparation Guide

> **Document ID**: `DELIV-08`  
> **Classification**: Oral Examination & Viva Voce Defense Manual  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Target Audience**: Graduating Engineers, Technical Presenters, Faculty Evaluators  
> **Coverage**: 25 Rigorous Technical Questions with Complete Model Answers  

---

## Category 1: System Architecture & Framework Selection

---

### Q1: Why did you choose Django + PostgreSQL over the popular MERN (MongoDB, Express, React, Node.js) stack for SkillByte?
**Model Answer**:  
While the MERN stack is common for consumer CRUD applications, SkillByte’s core problem domain requires **strict transactional consistency and relational integrity**, which MongoDB’s document model does not guarantee without heavy application-level locking.

Specifically:
1. **Relational Consistency**: An assessment platform consists of deeply related relational structures—Users have Profiles; Questions have Options, Test Cases, Attempts, Answers, Submissions, and Results. Relational database constraints (`ON DELETE CASCADE`, `unique_together`) ensure orphan records never corrupt exam grading.
2. **ACID Transactions**: When an assessment is submitted, grading updates the attempt status, writes submissions, calculates percentage scores, and updates leaderboard standings. Django’s `transaction.atomic()` ensures all steps succeed together or roll back entirely.
3. **Built-in Security Kernel**: Django provides industry-leading default protections against Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF), and SQL injection through its ORM query parameterization, significantly reducing the attack surface.

---

### Q2: Why is the architecture described as a "Monolithic REST" pattern rather than a fully decoupled Single Page Application (SPA)?
**Model Answer**:  
A pure SPA (e.g., React with Vite) paired with a separate API backend introduces substantial complexity: CORS management, client-side route duplication, complex state management libraries (Redux/Zustand), and heavy frontend build toolchains.

By adopting a **Monolithic REST pattern**:
1. Django acts as the central orchestrator, directly serving base HTML5 templates containing responsive Bootstrap 5.3 layouts and the Monaco Editor bundle.
2. Lightweight, modern ES6 JavaScript controllers dynamically make asynchronous `fetch()` calls to Django REST Framework (DRF) endpoints using Bearer JWT tokens.
3. This delivers the seamless, non-reloading user experience of an SPA (such as instantaneous code execution in Monaco and dynamic leaderboard filtering) while preserving the operational simplicity, rapid page rendering, and integrated security of a monolithic Django framework.

---

### Q3: How does the system achieve loose coupling with the Judge0 code execution engine?
**Model Answer**:  
Judge0 is integrated strictly as an **external microservice** communicating over standard HTTP REST. The application core interacts with Judge0 exclusively via an adapter class (`Judge0Service` in `questions/judge0_service.py`).

1. **Protocol Decoupling**: Django submits source code via `POST /submissions` and receives an asynchronous tracking token. Django then polls the submission endpoint (`GET /submissions/{token}`) until execution completes or times out (30 seconds).
2. **Fault Isolation**: If the Judge0 Docker service crashes or becomes unreachable, Django catches the network exception (`requests.exceptions.RequestException`) and returns an explicit `SERVICE_UNAVAILABLE` verdict with a user-friendly error message, preventing application server crashes.

---

### Q4: What role does PostgreSQL play, and why did the SRS prohibit SQLite even during early development?
**Model Answer**:  
SQLite relies on file-level locking during write operations. In an assessment environment where multiple students submit answers or run code simultaneously, SQLite frequently throws `database is locked` errors, causing dropped submissions and corrupted attempt state.

Furthermore, PostgreSQL provides:
- **Native JSONField / JSONB**: Powers the multi-language starter code templates for Python, Java, and C++ within a single column without requiring extra relational tables.
- **Advanced Indexing**: B-tree indexing on compound fields (`category`, `difficulty`, `is_active`, `status`) ensures lightning-fast queries during live exams.
- **Production Parity**: Enforcing PostgreSQL in development eliminated the classic "works on my machine" deployment defects often caused by SQLite's loose type affinity.

---

### Q5: How do you balance stateless JWT API authentication with Django's traditional session management?
**Model Answer**:  
SkillByte utilizes a **hybrid authentication approach**:
1. **Stateless JWT for Dynamic Features**: Interactive student flows (submitting code from Monaco, polling attempt status, rating questions, updating profiles) communicate over REST using standard `Authorization: Bearer <token>` headers via SimpleJWT. This ensures the API remains horizontally scalable without shared session server overhead.
2. **Session Security for Administrative Interfaces**: The Django administrative dashboard (`/admin/`) utilizes standard HTTP-only session cookies with strict CSRF protection.
3. **Token Blacklisting**: To prevent the classic flaw of stateless JWTs (inability to revoke compromised tokens), SkillByte implements SimpleJWT's `token_blacklist` app. When a student logs out or rotates their refresh token, the prior token is immediately blacklisted in PostgreSQL.

---

### Q6: What is the purpose of Gunicorn and Nginx in the production architecture?
**Model Answer**:  
Django's built-in `manage.py runserver` is single-threaded and intended solely for development. In production:
1. **Gunicorn (Green Unicorn)**: Acts as a production WSGI HTTP server running multiple worker processes (typically $2 \times \text{vCPUs} + 1$) to handle concurrent Python execution and database queries.
2. **Nginx**: Acts as the internet-facing reverse proxy. It terminates SSL/TLS (HTTPS), buffers slow clients, protects Gunicorn from slow-loris attacks, compresses HTTP responses via Gzip, and directly serves static assets (CSS, JS, images, Monaco bundles) directly from disk, freeing Python processes from static file I/O.

---

## Category 2: Sandboxing, Code Execution & Security

---

### Q7: How does SkillByte prevent malicious student code (e.g., `os.system("rm -rf /")` or fork bombs) from compromising the host server?
**Model Answer**:  
Student code is **never executed directly on the host operating system**. Instead, code execution occurs inside isolated, throwaway Linux containers managed by Judge0.

The sandbox applies defense-in-depth isolation:
1. **Unprivileged User**: Code runs as `nobody` (UID 65534), which has zero administrative privileges and cannot modify system files.
2. **Linux Control Groups (cgroups)**:
   - **CPU Throttling**: A hard 2.0-second CPU time quota terminates infinite loops (`while True: pass`) via `SIGKILL`.
   - **Memory Quotas**: A 256 MB memory limit terminates memory bombs (`x = [0] * 10**9`) via the kernel OOM killer.
   - **Process Limits**: A PID ceiling (e.g., maximum 64 processes) completely neutralizes fork bombs.
3. **Severed Egress Networking**: Containers are launched with `--net none`. Socket creation fails, preventing DDoS attacks, port scanning, and outbound data exfiltration.

---

### Q8: How do you prevent students from viewing hidden test cases or answer keys through browser network inspection?
**Model Answer**:  
SkillByte enforces **Zero-Leakage Data Sanitization** at the serializer layer:
1. **MCQ Questions**: During active assessments, `QuestionOptionSerializer` explicitly excludes the `is_correct` boolean field. The client only receives the option text and key. The server evaluates answers only upon final submission.
2. **Coding Challenges**: The `TestCaseSerializer` filters queryset results with `test_cases.filter(is_hidden=False)`. Students only see public sample test cases. Hidden test cases used for final grading are queried exclusively server-side inside `CodingAssessmentSubmitView` and are never exposed via any public API.

---

### Q9: How are race conditions and double submissions prevented in timed assessments?
**Model Answer**:  
Race conditions (such as double-clicking the submit button or firing simultaneous submission requests) are prevented using:
1. **Database Row-Level Locking**: Views utilize `select_for_update()` inside `transaction.atomic()` blocks when retrieving the `AssessmentAttempt`.
2. **Strict State Transitions**: The submit handler verifies that `attempt.status == AttemptStatus.IN_PROGRESS`. Once the first request acquires the row lock, it transitions the status to `COMPLETED`. Any subsequent concurrent request is immediately rejected because the status is no longer `IN_PROGRESS`.

---

### Q10: How does the server-authoritative timer work? Can a student pause or extend their time by modifying client JavaScript?
**Model Answer**:  
No, modifying the client timer has **zero effect on grading**.
- The client-side countdown timer in JavaScript is purely visual to assist the candidate's pacing.
- The server records the immutable timestamp `started_at` in the database when the attempt is created.
- Upon receiving a submission, the server computes:
  $$\Delta t = \text{now}() - \text{started\_at}$$
- If $\Delta t > \text{time\_limit\_seconds} + \text{grace\_period}$, the server automatically rejects the submission or marks the score as zero, irrespective of what the client claims.

---

### Q11: What hashing algorithm is used for student passwords, and how does it prevent rainbow table attacks?
**Model Answer**:  
SkillByte utilizes Django’s default **PBKDF2 with HMAC-SHA256**:
- It applies **600,000 hashing iterations**, deliberately making brute-force computation computationally expensive.
- Each password is combined with a unique, cryptographically random **128-bit salt** generated via `os.urandom()`.
- Because every user has a distinct salt, precomputed rainbow tables are rendered completely useless, even if two users choose the exact same password.

---

### Q12: How is rate limiting enforced against denial-of-service or brute force attacks?
**Model Answer**:  
Rate limiting is enforced at the API gateway layer using Django REST Framework's Throttling engine:
- **Authentication endpoints** (`/api/auth/login/`, `/register/`) are throttled to **15 requests per minute** to thwart dictionary attacks.
- **Code execution endpoints** (`/api/assessments/coding/<id>/run/`) are throttled to **30 requests per minute** to prevent Judge0 container starvation.
- **Unauthenticated requests** are throttled to **120 requests per minute**, and authenticated users to **1200 requests per minute**.
- Requests exceeding these limits return `HTTP 429 Too Many Requests` with a standard `Retry-After` header.

---

## Category 3: Scoring, Gamification & Data Integrity

---

### Q13: Explain the "Best Score per Unique Question" deduplication algorithm in Unified Scoring.
**Model Answer**:  
Traditional platforms that sum all points from every submission suffer from "score farming," where candidates repeatedly submit trivial questions to artificially inflate their ranking.

SkillByte solves this with the **Best Score per Unique Question** deduplication model implemented in `questions/scoring_service.py`:
$$\text{Total Points} = \sum_{q \in \text{Unique Solved Questions}} \max(\text{score}_{q})$$
- When computing a student's standing, the service groups all completed attempts by `question_id`.
- For each unique question, it extracts only the highest marks achieved.
- Submitting a 10-mark question ten times will yield exactly 10 points toward the student's overall profile, completely eliminating score inflation.

---

### Q14: How are skill tiers calculated and what are the point thresholds?
**Model Answer**:  
Skill tiers are dynamically assigned based on the candidate's deduplicated cumulative points:
- **Novice** (0 – 49 points): Beginner stage, demonstrated by solving introductory MCQs and simple syntax problems.
- **Apprentice** (50 – 149 points): Intermediate stage, reflecting mastery of standard algorithmic problems and core CS theory.
- **Specialist** (150 – 299 points): Advanced stage, demonstrated by solving medium-to-hard coding problems across multiple categories (Python, Java, DSA).
- **Master** (300+ points): Expert stage, reflecting comprehensive domain mastery across both theoretical and practical coding domains.

---

### Q15: How does the dynamic leaderboard support filtering by category and timeframe without corrupting historical rankings?
**Model Answer**:  
The leaderboard endpoint (`/api/leaderboard/`) computes rankings dynamically via queryset filtering:
1. **Timeframe Filtering**: Filters attempts using `submitted_at__gte = now() - timedelta(days=7)` for weekly rankings, or `30 days` for monthly rankings.
2. **Category Filtering**: Filters attempts matching `category__iexact = category`.
3. The deduplication algorithm is then applied exclusively to the filtered subset of attempts, ensuring that a student’s rank within "Python this month" reflects only their genuine, deduplicated Python achievements within that specific 30-day window.

---

### Q16: How does the platform handle partial credit in coding problems?
**Model Answer**:  
SkillByte implements proportional partial credit scoring:
$$\text{Awarded Marks} = \left(\frac{\text{Passed Test Cases}}{\text{Total Test Cases}}\right) \times \text{Question Weight}$$
For example, if a 10-mark question has 5 test cases and the candidate's solution passes 3 sample cases but fails 2 hidden edge cases, the system awards:
$$\text{Score} = \left(\frac{3}{5}\right) \times 10 = 6.0 \text{ marks}$$
The submission status is tagged as `PARTIAL`, giving students positive reinforcement for partial algorithmic progress.

---

### Q17: What failure tags does the system generate when code execution fails, and why?
**Model Answer**:  
When code fails to achieve an `ACCEPTED` verdict, SkillByte categorizes the failure into industry-standard diagnostic tags:
1. **`COMPILATION_ERROR`**: Source code failed to compile (syntax errors, missing semicolons, import errors).
2. **`RUNTIME_ERROR`**: Exception raised during execution (e.g., `IndexError`, `ZeroDivisionError`, `NullPointerException`, segmentation faults).
3. **`TIME_LIMIT_EXCEEDED`**: Execution exceeded the allowed CPU time limit (typically 2.0s), indicating suboptimal time complexity (e.g., $O(N^2)$ instead of $O(N \log N)$).
4. **`WRONG_ANSWER`**: Code executed successfully within time/memory limits, but standard output mismatched expected output.

---

## Category 4: Assessment Lifecycle & Resilience

---

### Q18: What happens if a student's browser crashes or network disconnects during an assessment?
**Model Answer**:  
SkillByte implements robust **Assessment Resumption** (Phase 11):
- When a student navigates back to the platform, the client calls `GET /api/assessments/active/`.
- If an incomplete attempt exists where `status == IN_PROGRESS` and time has not expired, the server returns the active `attempt_id`, the selected questions, and the remaining time:
  $$\text{time\_remaining} = \text{time\_limit\_seconds} - (\text{now}() - \text{started\_at})$$
- The frontend seamlessly restores the Monaco editor state and resumes the countdown timer without restarting the assessment clock.

---

### Q19: How does assessment abandonment work?
**Model Answer**:  
If a candidate wishes to terminate an assessment early:
1. They click "Abandon Assessment" and confirm via a confirmation modal.
2. The client fires `POST /api/assessments/<id>/abandon/`.
3. The server validates ownership, transitions the attempt status to `ABANDONED`, locks the session from further submissions, and awards 0 marks.
4. This ensures clean session closure without leaving orphaned sessions in the active attempt pool.

---

### Q20: How are guest attempts differentiated from registered student attempts in the database?
**Model Answer**:  
In `questions_assessmentattempt`:
- **Student Attempts**: `user_id` contains the foreign key referencing `auth_user.id`, and `session_id` is blank.
- **Guest Attempts**: `user_id` is `NULL`, and `session_id` stores a unique cryptographic UUID string.
- This allows guests to experience assessments in sandboxed mode while cleanly isolating their transient data from permanent student leaderboards and academic transcripts.

---

### Q21: How does the platform handle server-side errors gracefully?
**Model Answer**:  
In Phase 11, custom error handlers were implemented:
- `handler404 = 'api.views.custom_404_view'`
- `handler403 = 'api.views.custom_403_view'`
- `handler500 = 'api.views.custom_500_view'`
Instead of exposing default Django technical debug screens (which leak internal file paths, framework versions, and database schemas), SkillByte renders custom, branded HTML5 error pages consistent with the platform's theme, directing users back to the dashboard.

---

## Category 5: Engineering Process & Quality Assurance

---

### Q22: How many automated tests exist in SkillByte, and what do they verify?
**Model Answer**:  
SkillByte is verified by **68 comprehensive automated unit and integration tests** distributed across 5 suites:
1. `questions.tests_phase11` (12 tests): Profile management, password change, assessment resumption, abandonment, CSV export RBAC, custom error pages, throttling.
2. `questions.tests_phase10` (11 tests): Unified scoring deduplication, skill tiers, leaderboard timeframe/category filtering, admin analytics KPIs, Run Code execution.
3. `questions.tests_phase9` (15 tests): Admin Question Bank CRUD, option validation, test case management, active toggling, soft deletion.
4. `questions.tests` (16 tests): Public question catalog, MCQ start/submit, coding start/submit, scoring calculations.
5. `accounts.tests` (14 tests): User registration, JWT login (username and email), token refresh, token blacklisting, RBAC enforcement, guest session tracking.
All 68 tests run in approximately 75 seconds and pass with 100% success.

---

### Q23: What is Chrome DevTools Protocol (CDP) verification, and why was it performed?
**Model Answer**:  
Automated Python unit tests verify backend logic and HTTP responses, but cannot test in-browser JavaScript behavior, Monaco editor rendering, or DOM updates.

To achieve true end-to-end verification, we performed **headless Chrome automation using the Chrome DevTools Protocol (CDP)** across 10 critical user journeys (profile editing, password change, mobile navbar toggle, assessment resumption, code download, CSV export). CDP allowed us to programmatically inspect the browser DOM, simulate realistic clicks, verify file downloads, and monitor browser console output, proving that all views operate with **zero JavaScript console errors**.

---

### Q24: What was the significance of Git checkpointing throughout the engineering lifecycle?
**Model Answer**:  
SkillByte was engineered following a strict phase-based milestone approach. At each phase boundary, automated test suites and CDP scenarios were verified before creating atomic, descriptive Git checkpoints.

This culminated in the final release tag:
- **Tag**: `v1.0.0-final-release`
- **Commit**: `9e66eef` (*"feat: complete phase 11 production polish and hardening"*)
This ensures that the software baseline is permanently locked and reproducible, while Phase 12 focuses purely on academic documentation and presentation assets.

---

### Q25: If given another semester, what future technical enhancements would you architect for SkillByte?
**Model Answer**:  
If expanding SkillByte into a commercial or institutional SaaS platform, our architectural roadmap includes:
1. **Real-Time Collaborative Duels**: Integrating Django Channels (WebSockets) and Redis to support 1-on-1 head-to-head live coding battles.
2. **Plagiarism Detection**: Integrating an automated source-code similarity engine (such as the MOSS algorithm) to detect copied solutions.
3. **AI-Assisted Code Hints**: Leveraging LLM APIs to provide context-aware debugging hints without revealing the full solution.
4. **Automated Proctoring**: Integrating browser tab-focus monitoring and optional webcam anomaly detection for high-stakes university examinations.

