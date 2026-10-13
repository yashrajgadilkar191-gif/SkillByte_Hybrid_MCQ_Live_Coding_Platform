# SKILLBYTE — Live Demonstration Script & Defense Runbook

> **Document ID**: `DELIV-07`  
> **Classification**: Presentation Runbook & Demonstration Script  
> **Release Target**: SkillByte v1.0.0 (`v1.0.0-final-release`)  
> **Target Duration**: Exactly 12 Minutes (+ 3 Minutes Buffer for Panel Q&A)  
> **Audience**: External Examiners, Evaluation Committee, Faculty Guides  

---

## 1. Pre-Demonstration Setup & Verification Checklist

Complete this checklist 15 minutes before calling the evaluation committee:

### 1.1 Service & Database Verification
- [ ] **Django Web Server**: Running on `http://127.0.0.1:8000/`.
  ```bash
  cd backend && python manage.py runserver 127.0.0.1:8000
  ```
- [ ] **PostgreSQL Database**: Port `5432` operational, `skillbyte_db` responsive.
- [ ] **Judge0 Sandbox Service**: Port `2358` healthy.
  ```bash
  curl http://localhost:2358/system_info
  ```

### 1.2 Seeded Accounts for Defense
| Role | Username | Password | Purpose |
|---|---|---|---|
| **Student** | `student1` | `password123` | Demonstrates student workflow, dashboard, Monaco, and leaderboard. |
| **Administrator** | `admin` | `adminpassword` | Demonstrates question bank CRUD, KPI charts, and CSV analytics export. |

### 1.3 Browser Preparation
- Launch Google Chrome in **Incognito / Private Mode** (prevents stale cookies or cached tokens).
- Set viewport zoom to **100%**; open DevTools console (`F12`) on a second screen to demonstrate **0 console errors**.

---

## 2. Minute-by-Minute Live Demonstration Script

```
0:00 ──── 1:30 ── Platform Introduction & Guest Experience
1:30 ──── 3:30 ── Student Login & Unified Mastery Dashboard
3:30 ──── 6:30 ── Live Coding Assessment in Monaco IDE
6:30 ──── 8:00 ── Result Telemetry, Failure Tags & Solution Utilities
8:00 ──── 9:30 ── Deduplicated Leaderboard & Attempt History
9:30 ──── 11:00 ── Admin Question Bank & Analytics CSV Export
11:00 ─── 12:00 ── Production Hardening & Branded Error Pages
```

---

### Phase 1: Platform Introduction & Guest Experience (0:00 – 1:30)

#### Actions:
1. Open `http://127.0.0.1:8000/`.
2. Scroll through the landing page highlighting the hero headline: *"Where Theory Meets Practice"*.
3. Click the **"Practice as Guest"** button.
4. Select category **"Mathematics"** and difficulty **"Easy"**; click **"Start Assessment"**.
5. Answer 3 multiple-choice questions; submit the assessment.

#### Presenter Speaking Script:
> *"Respected committee members and examiners, welcome to our demonstration of **SKILLBYTE**.
> 
> In traditional technical recruitment and university assessments, candidates are typically evaluated through one of two extremes: either pure theoretical multiple-choice quizzes that fail to test practical coding competence, or competitive programming platforms like LeetCode that ignore foundational computer science principles.
> 
> SkillByte bridges this divide with a unified, hybrid assessment architecture. Notice that as an unauthenticated guest, I can immediately start practice assessments without mandatory registration. The system assigns a cryptographically unique session ID, preserving friction-free onboarding while safeguarding core data."*

---

### Phase 2: Student Authentication & Unified Dashboard (1:30 – 3:30)

#### Actions:
1. Click **"Login"** in the top navigation bar.
2. Enter username `student1` and password `password123`; click **"Sign In"**.
3. Arrive at the **Unified Dashboard** (`/dashboard/`).
4. Point out the **Overall Points**, **Theory Mastery Bar**, **Practical Coding Mastery Bar**, and **Skill Tier Badge** (*"Apprentice"*).

#### Presenter Speaking Script:
> *"Now we log in as an authenticated student, `student1`. Notice that the authentication flow generates a JSON Web Token pair with automatic rotation and blacklisting.
> 
> Here on the student dashboard, we see the heart of our platform: **Unified Mastery Tracking**. Rather than displaying a raw, meaningless test score, SkillByte calculates a candidate's mastery across two distinct vectors: Theory and Practice.
> 
> `student1` currently holds 85 total points, categorizing them into the **Apprentice** tier. As they solve more advanced problems across different subjects, the system dynamically promotes them through **Specialist** and ultimately **Master**."*

---

### Phase 3: Live Monaco Coding Environment (3:30 – 6:30)

#### Actions:
1. Navigate to **"Coding Assessments"** (`/coding/`).
2. Select the problem **"Two Sum"** in the **Python** category; click **"Start Assessment"**.
3. Point out the embedded **Monaco Editor**, the syntax highlighting, the active countdown timer, and the language selector.
4. Click **"Run Code"** with the default starter template. Point out the public sample test cases passing.
5. Introduce an intentional syntax error (e.g., remove a colon `:` from a loop definition); click **"Run Code"**.
6. Show the real-time compiler diagnostic output in the terminal pane.
7. Correct the code with the optimal hash-map solution:
   ```python
   def solution(nums, target):
       seen = {}
       for i, num in enumerate(nums):
           diff = target - num
           if diff in seen:
               return [seen[diff], i]
           seen[num] = i
   ```
8. Click **"Submit Solution"**.

#### Presenter Speaking Script:
> *"Now we move into the live coding environment. We integrated Microsoft's **Monaco Editor**—the exact engine powering VS Code—directly into the browser.
> 
> When I click **'Run Code'**, SkillByte dispatches the code to our self-hosted **Judge0 sandbox** running inside an isolated Docker container on port 2358. Within 30 milliseconds, the code is compiled, executed against public sample test cases, and the stdout is returned to the browser.
> 
> Notice what happens when I introduce a syntax error: the sandbox captures the compiler's diagnostic output without crashing the server.
> 
> When the student is confident, they click **'Submit Solution'**. At this stage, the code is evaluated against hidden test cases that are never transmitted to the browser, guaranteeing absolute exam integrity."*

---

### Phase 4: Result Telemetry, Failure Tags & Solution Utilities (6:30 – 8:00)

#### Actions:
1. Land on the **Coding Result Page** (`/coding/result/<id>/`).
2. Point out the verdict badge (**ACCEPTED**), execution time (**0.04s**), memory usage (**8.4 MB**), and test case score (**5 / 5 Passed**).
3. Demonstrate Phase 11 production utilities:
   - Click **"Copy Solution"** $\rightarrow$ show the green feedback toast: *"Code copied to clipboard!"*.
   - Click **"Download Code"** $\rightarrow$ show the local browser download of `solution.py`.
   - Click **"Practice Again"** $\rightarrow$ demonstrate the option to retry or practice with another language.

#### Presenter Speaking Script:
> *"Upon submission, the candidate receives comprehensive performance telemetry. Notice the verdict: **ACCEPTED**, 5 out of 5 test cases passed, execution completed in 40 milliseconds, with an exact memory footprint of 8.4 megabytes.
> 
> If the solution had exceeded the 2.0-second CPU quota or failed on edge cases, SkillByte would assign explicit failure tags: `TIME_LIMIT_EXCEEDED`, `RUNTIME_ERROR`, or `WRONG_ANSWER`.
> 
> In Phase 11, we added student utility controls: with one click, candidates can copy their solution, download it as a native source file with the appropriate `.py`, `.java`, or `.cpp` extension, or re-attempt the challenge."*

---

### Phase 5: Deduplicated Leaderboard & Attempt History (8:00 – 9:30)

#### Actions:
1. Click **"Leaderboard"** in the top navigation bar (`/leaderboard/`).
2. Point out the student rankings, avatar badges, and skill tiers.
3. Demonstrate dynamic filtering:
   - Filter by Category: Select **"Python"**.
   - Filter by Timeframe: Select **"This Month"**.
4. Navigate to **"My Attempts"** (`/attempts/`) to display historical session logs.

#### Presenter Speaking Script:
> *"A frequent flaw in competitive scoring platforms is 'score inflation'—where a candidate repeatedly solves the easiest problem 50 times to farm points.
> 
> SkillByte implements a strict **Best Score per Unique Question** deduplication algorithm. If a student attempts 'Two Sum' three times and scores 4, 8, and 10 points, only the maximum score of 10 is added to their cumulative standing.
> 
> Candidates can filter rankings by timeframe and subject, rewarding breadth of mastery rather than repetitive grinding."*

---

### Phase 6: Admin Question Bank & Analytics CSV Export (9:30 – 11:00)

#### Actions:
1. Log out as `student1`; log in as `admin` (`adminpassword`).
2. Navigate to **"Admin Question Bank"** (`/admin/questions/`).
3. Show the question table with status badges (`Active` / `Inactive`), category filters, and action buttons (`Edit`, `Toggle Status`, `Delete`).
4. Navigate to **"Platform Analytics"** (`/admin/analytics/`).
5. Highlight the platform KPIs: Total Registered Users, Total Attempts, Completion Rate (88.9%), Average MCQ Score, and Average Coding Score.
6. Click the **"Export CSV"** button $\rightarrow$ confirm the download of `skillbyte_analytics_summary.csv`.

#### Presenter Speaking Script:
> *"Now we transition to the administrative interface. The Question Bank provides full CRUD operations for both MCQ theoretical questions and complex coding challenges. Admins can configure memory limits, CPU timeouts, language starter templates, and hidden test cases.
> 
> On the Analytics dashboard, faculty members and recruiters gain instant macro-level visibility into platform engagement, completion rates, and average subject proficiencies.
> 
> In Phase 11, we added server-side CSV export capability: with a single click, administrators can export institutional performance data for academic record-keeping."*

---

### Phase 7: Production Hardening Showcase (11:00 – 12:00)

#### Actions:
1. Navigate to **"Profile Settings"** (`/profile/`).
2. Demonstrate profile metadata editing and the secure password change modal.
3. Intentionally enter an unmapped URL in the address bar: `http://127.0.0.1:8000/invalid-page-for-demo/`.
4. Showcase the custom, branded SkillByte **404 Page** (with "Return to Home" button).
5. Open Chrome DevTools Console (`F12`) to verify **zero JavaScript errors**.
6. Conclude the demonstration and invite committee questions.

#### Presenter Speaking Script:
> *"Finally, we highlight our Phase 11 production polish and hardening. Notice our responsive profile management and secure password change workflows.
> 
> If a user enters an invalid URL or encounters an authorization barrier, SkillByte does not expose raw framework debug stacktraces. Instead, it renders branded, informative error templates.
> 
> Throughout this entire demonstration across all views, our browser console has maintained exactly zero errors.
> 
> In summary, SkillByte has completed 42 out of 42 SRS requirements, verified across 68 automated unit and integration tests and 10 end-to-end browser scenarios. We are now ready to take your questions."*

---

## 3. Examiner Defense Contingency Protocols

| Potential Live Demo Glitch | Rapid Contingency Procedure |
|---|---|
| **Port 8000 already in use** | Run `netstat -ano \| findstr :8000` $\rightarrow$ kill occupying PID $\rightarrow$ restart Django. |
| **Judge0 Docker container unresponsive** | Execute `docker restart judge0-server` $\rightarrow$ verify with `curl http://localhost:2358/system_info`. |
| **Accidental browser cache issue** | Press `Ctrl + Shift + R` (Hard Reload) or switch to a fresh Incognito tab. |
| **Accidental student logout** | Click "Login" and use pre-filled saved credentials for `student1`. |

