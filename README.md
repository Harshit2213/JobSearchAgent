================================================================================
  JOB SEARCH AGENT
  Multi-agent AI system for job discovery, matching, and application prep
================================================================================


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROJECT DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job Search Agent is a self-hosted web application that automates the full job
search workflow using a pipeline of AI agents. The user uploads their resume
(PDF or DOCX), and the system:

  1. Parses the resume into a structured profile
  2. Infers suitable job titles (if none is given)
  3. Searches four job boards simultaneously for live listings
  4. Scores and ranks every listing against the resume
  5. For any chosen job, generates:
       - A tailored cover letter and rewritten resume bullets
       - A company research report (green flags, red flags)
       - 8 personalised interview Q&A pairs
  6. Persists saved applications in a local SQLite tracker

The backend uses Anthropic Claude (claude-sonnet-4-6) as the primary AI with
Groq (llama-3.3-70b-versatile) as an optional fast backend and automatic
failover. A circuit breaker routes traffic away from Anthropic when it detects
repeated failures (rate limits, credit exhaustion, auth errors).


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TECH STACK & DEPENDENCIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Language          Python 3.11+

  Web Framework     FastAPI 0.115.6
                    Uvicorn 0.32.1 (ASGI server)
                    Jinja2 3.1.5 (server-side templates)
                    python-multipart 0.0.20 (file upload handling)

  AI / LLM
    Primary         anthropic 0.40.0  →  Claude Sonnet 4.6
    Fallback        openai >=1.0 SDK  →  Groq (llama-3.3-70b-versatile)
                    (Groq uses the OpenAI-compatible REST API)

  Data / ORM        SQLAlchemy 2.0.36 + SQLite (no external DB required)
                    Pydantic 2.10.3 + pydantic-settings 2.7.0

  File Parsing      pdfplumber 0.11.4 (PDF text extraction)
                    python-docx 1.1.2 (DOCX text extraction)
                    filetype 1.2.0 (MIME-type validation by magic bytes)

  HTTP Client       httpx 0.28.1 (async calls to job board APIs)

  Rate Limiting     slowapi 0.1.9 (10 req/min per IP on all API routes)

  Frontend          Vanilla HTML / CSS / JavaScript (no framework)
                    Single-page app driven by fetch() calls to the REST API

  All Python dependencies are pinned in requirements.txt.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FOLDER STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  JobSearchAgent/
  │
  ├── main.py                   FastAPI app entry point; mounts routers,
  │                             static files, and templates; runs init_db()
  │                             on startup
  │
  ├── requirements.txt          Pinned Python dependencies
  ├── .env.example              Template for the required .env file
  ├── .env                      Your local secrets (gitignored — never commit)
  ├── .gitignore
  │
  ├── agents/                   AI agent layer
  │   ├── base.py               BaseAgent: wraps BackendRouter for _call()
  │                             and _acall(); subclasses set _quality
  │   ├── orchestrator.py       OrchestratorAgent: wires the full pipeline
  │                             (parse → infer → discover → score)
  │   ├── resume_parser.py      Extracts structured profile from PDF/DOCX
  │                             using Claude tool use (quality=high)
  │   ├── role_inference.py     Suggests 3-5 job titles from the profile
  │                             (quality=fast → Groq)
  │   ├── job_discovery.py      Fans out to 4 job boards concurrently
  │   ├── job_matching.py       Scores each listing vs. the resume with 20x
  │                             async concurrency (quality=fast → Groq)
  │   ├── tailoring.py          Rewrites resume bullets + writes cover letter
  │                             (quality=high → Claude)
  │   ├── research.py           Analyses a JD for company insights, green
  │                             flags, red flags (quality=fast → Groq)
  │   ├── interview_prep.py     Generates 8 personalised interview Q&As
  │                             (quality=fast → Groq)
  │   └── tracker.py            CRUD wrapper over the applications DB table
  │
  ├── backends/                 LLM abstraction layer
  │   ├── base.py               LLMBackend Protocol (typing contract)
  │   ├── anthropic_backend.py  Calls claude-sonnet-4-6; handles prompt
  │                             caching (cache_control=ephemeral); maps
  │                             Anthropic errors to HTTPException
  │   ├── groq_backend.py       Calls Groq via the OpenAI SDK; adapts
  │                             Anthropic tool format to OpenAI format;
  │                             maps errors to HTTPException
  │   ├── router.py             BackendRouter: Strategy + Circuit Breaker.
  │                             quality="high" → Anthropic (Groq fallback)
  │                             quality="fast" → Groq directly
  │   └── circuit_breaker.py   Three-state machine (CLOSED/OPEN/HALF_OPEN);
  │                             trips on 3 consecutive Anthropic failures;
  │                             auto-recovers after 60 s
  │
  ├── integrations/             Job board API clients (all async)
  │   ├── adzuna.py             Adzuna — supports title + location search;
  │                             returns salary data; requires API credentials
  │   ├── remotive.py           Remotive — remote-only jobs; free API
  │   ├── the_muse.py           The Muse — category-based search; free API
  │   └── arbeitnow.py          Arbeitnow — keyword search; free API
  │
  ├── routers/                  FastAPI route handlers
  │   ├── resume.py             POST /api/upload-resume
  │   ├── jobs.py               POST /api/search-jobs
  │                             POST /api/jobs/tailor
  │                             POST /api/jobs/research
  │   ├── interview.py          POST /api/jobs/interview-prep
  │   └── applications.py       POST/GET /api/applications
  │                             PUT  /api/applications/{id}/status
  │
  ├── models/                   Pydantic data models
  │   ├── resume.py             ParsedResume
  │   ├── job.py                JobListing, JobScore, MatchedJob,
  │                             TailoredApplication, CompanyResearch,
  │                             InterviewPrep, QAPair
  │   └── application.py        ApplicationCreate/Update/Out, ApplicationStatus
  │
  ├── db/                       Persistence layer
  │   └── database.py           SQLAlchemy engine + session factory;
  │                             ApplicationRow ORM model; CRUD helpers;
  │                             SQLite stored at data/jobs.db
  │
  ├── utils/
  │   ├── config.py             pydantic-settings Settings class — reads
  │                             all env vars from .env
  │   ├── file_security.py      validate_upload(): size check + MIME-type
  │                             validation by magic bytes (not extension)
  │   ├── limiter.py            slowapi Limiter singleton
  │   └── text.py               strip_html(), truncate() helpers used by
  │                             all job board integrations
  │
  ├── templates/
  │   └── index.html            Single-page HTML shell with four sections:
  │                             Upload, Roles, Jobs grid, Tracker table,
  │                             plus a slide-in job detail panel
  │
  ├── static/
  │   ├── css/style.css         All UI styles
  │   └── js/app.js             All client-side logic: form submission,
  │                             job rendering, lazy-load tabs, tracker
  │
  └── data/
      └── jobs.db               SQLite database (auto-created; gitignored)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ENVIRONMENT VARIABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Copy .env.example to .env and fill in the values below.
  The .env file is gitignored — never commit it.

  REQUIRED
  ────────
  ANTHROPIC_API_KEY          Your Anthropic API key.
                             Get one at https://console.anthropic.com
                             Used by the resume parser and tailoring agent
                             (quality="high" routes).

  ADZUNA_APP_ID              Adzuna application ID.
  ADZUNA_APP_KEY             Adzuna application key.
                             Free registration at https://developer.adzuna.com
                             Used by the Adzuna job board integration.

  OPTIONAL
  ────────
  GROQ_API_KEY               Groq API key (free tier available).
                             Get one at https://console.groq.com
                             When set, role inference, job matching, research,
                             and interview prep use Groq instead of Claude,
                             making them faster and cheaper.
                             Also acts as a fallback when Anthropic is
                             unavailable (circuit breaker trips).

  GROQ_MODEL                 Groq model ID.
                             Default: llama-3.3-70b-versatile

  CIRCUIT_BREAKER_THRESHOLD  Number of consecutive Anthropic failures before
                             routing falls back to Groq.
                             Default: 3

  CIRCUIT_BREAKER_TIMEOUT    Seconds before the circuit attempts recovery.
                             Default: 60

  ADZUNA_COUNTRY             Two-letter country code for Adzuna searches.
                             Default: us

  MAX_JOBS_PER_SOURCE        Maximum listings fetched from each job board.
                             Default: 25  (100 total across 4 sources)

  MAX_UPLOAD_BYTES           Maximum resume file size in bytes.
                             Default: 5242880  (5 MB)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Prerequisites: Python 3.11 or later.

  1. Clone or download the repository.

  2. Create and activate a virtual environment:

       python -m venv .venv

       # Windows (PowerShell)
       .venv\Scripts\Activate.ps1

       # macOS / Linux
       source .venv/bin/activate

  3. Install dependencies:

       pip install -r requirements.txt

  4. Set up environment variables:

       # Windows
       copy .env.example .env

       # macOS / Linux
       cp .env.example .env

     Open .env in any editor and fill in at minimum:
       ANTHROPIC_API_KEY
       ADZUNA_APP_ID
       ADZUNA_APP_KEY

     Optionally add GROQ_API_KEY for faster and cheaper AI calls.

  5. The SQLite database is created automatically on first run.
     No database setup step is required.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOW TO RUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Start the development server from the project root:

    uvicorn main:app --reload

  The app is now available at:

    http://localhost:8000

  The auto-generated interactive API docs (Swagger UI) are at:

    http://localhost:8000/docs

  To run on a different port:

    uvicorn main:app --reload --port 8080

  To bind to all interfaces (e.g. on a server or VM):

    uvicorn main:app --host 0.0.0.0 --port 8000

  Rate limits: every API route is capped at 10 requests/minute per IP.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REST API REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  POST /api/upload-resume
    Form data: file (PDF or DOCX), job_title (optional string)
    Returns: { profile, inferred_roles, job_title }
    Parses the resume and optionally infers target roles.

  POST /api/search-jobs
    Body: { job_title, location, profile }
    Returns: { jobs: [MatchedJob], total }
    Searches all job boards and scores each listing.

  POST /api/jobs/tailor
    Body: { job: JobListing, profile: ParsedResume }
    Returns: { original_bullets, tailored_bullets, cover_letter }
    Rewrites the resume and writes a cover letter for the chosen job.

  POST /api/jobs/research
    Body: { job: JobListing }
    Returns: { snapshot, green_flags, red_flags }
    Analyses the job description for company and role insights.

  POST /api/jobs/interview-prep
    Body: { job: JobListing, profile: ParsedResume }
    Returns: { qa_pairs: [{question, answer}, ...] }
    Generates 8 personalised interview questions with model answers.

  POST /api/applications
    Body: { job_title, company, job_url, source }
    Returns: ApplicationOut (201 Created)
    Saves a job to the application tracker.

  GET  /api/applications
    Returns: [ApplicationOut]
    Lists all saved applications, newest first.

  PUT  /api/applications/{id}/status
    Body: { status, notes }
    Returns: ApplicationOut
    Updates the status of a saved application.
    Valid statuses: saved | applied | phone_screen | interview | offer | rejected


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOW THE AGENT PIPELINE WORKS — END TO END
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STEP 1 — RESUME UPLOAD & PARSING
  ─────────────────────────────────
  The user submits their resume (PDF or DOCX) via the web form, with an
  optional job title.

  file_security.py validates the upload:
    - Rejects files larger than MAX_UPLOAD_BYTES (default 5 MB)
    - Validates the file type by reading magic bytes with the filetype
      library (not by checking the file extension, which can be spoofed)
    - Only PDF and DOCX are accepted

  ResumeParserAgent (quality=high → Claude) extracts the text:
    - PDF: pdfplumber extracts text from each page
    - DOCX: python-docx iterates paragraphs

  The raw text is sent to Claude with a structured tool ("extract_resume").
  Claude uses tool use to return a JSON object with:
    name, email, skills, tech_stack, years_of_experience,
    past_titles, education, summary

  This becomes a ParsedResume Pydantic model.

  STEP 2 — ROLE INFERENCE (when no title is provided)
  ────────────────────────────────────────────────────
  RoleInferenceAgent (quality=fast → Groq) receives the ParsedResume.
  It sends a condensed profile text to Groq with the "infer_roles" tool.
  Groq returns 3-5 concrete, searchable role titles ranked from best fit
  to reasonable stretch (e.g. "Senior Backend Engineer", "ML Engineer").

  The web UI renders these as clickable buttons. The user selects one.

  STEP 3 — JOB DISCOVERY
  ───────────────────────
  JobDiscoveryAgent fires four async HTTP requests in parallel (asyncio.gather):

    Adzuna    — paid API, supports location filter and salary data
    Remotive  — free API, remote-only jobs
    The Muse  — free API, category-based search
    Arbeitnow — free API, keyword search

  Each integration:
    - Calls its API via httpx.AsyncClient with a 10 s timeout
    - Normalises the response into JobListing Pydantic objects
    - Strips HTML from descriptions (utils/text.py)
    - Truncates descriptions to 4000 characters
    - Generates a stable ID from an MD5 hash of the job URL

  Results are deduplicated by URL and combined into a single list.
  Individual source failures are logged and skipped (the others continue).

  STEP 4 — JOB MATCHING & SCORING
  ─────────────────────────────────
  JobMatchingAgent (quality=fast → Groq) scores every listing concurrently.

  It builds a system prompt that embeds the full ParsedResume profile and a
  scoring rubric (0-100 scale: 90+ exceptional, 70-89 strong, 50-69 moderate,
  below 50 poor). Each job's title, company, location, and description are
  sent to Groq using the "score_job" tool.

  A semaphore limits concurrency to 20 simultaneous requests (Groq is fast
  enough that this is safe without hammering rate limits).

  Each call returns: score (int), strengths (list), missing_skills (list),
  summary (str). The results are wrapped in MatchedJob and sorted
  descending by score. Failed scorings get score=0 with a fallback message.

  The sorted list is returned to the UI, which renders a grid of job cards
  showing the score, top strengths, and top missing skills.

  STEP 5 — JOB DETAIL PANEL (lazy-loaded tabs)
  ──────────────────────────────────────────────
  Clicking any job card opens a slide-in panel. Tabs are lazy-loaded on
  first click and cached client-side to avoid redundant API calls.

    Summary tab (immediate, no API call):
      Shows the score badge, match summary, strengths, and skill gaps
      already present in the MatchedJob. Links to the original posting.

    Tailor tab  →  POST /api/jobs/tailor
      TailoringAgent (quality=high → Claude) receives the ParsedResume and
      the chosen JobListing. It uses the "tailor_application" tool to:
        - Select the 5 most relevant existing achievements from the profile
        - Rewrite each bullet to mirror the JD's vocabulary (no fabrication)
        - Draft a 3-paragraph cover letter with a personalised hook,
          skills/experience match, and culture-fit close
      Rendered as a before/after table and a formatted cover letter block.

    Research tab  →  POST /api/jobs/research
      ResearchAgent (quality=fast → Groq) analyses the job description text
      using the "research_company" tool. Returns:
        - snapshot: 2-3 sentence company overview inferred from the JD
        - green_flags: positive signals (growth, clear expectations, good culture)
        - red_flags: warning signals (vague scope, toxic language, unrealistic asks)
      Only text present in the JD is used — no external web searches.

    Interview Prep tab  →  POST /api/jobs/interview-prep
      InterviewPrepAgent (quality=fast → Groq) generates 8 Q&A pairs:
        - 3 behavioural questions (STAR format answers)
        - 3 technical/role-specific questions (based on JD requirements)
        - 2 company/culture-fit questions (based on JD signals)
      Answers reference the actual candidate's background, not generic advice.
      Rendered as a collapsible accordion for easy review.

  STEP 6 — APPLICATION TRACKER
  ──────────────────────────────
  The "Save to Tracker" button in any job panel POSTs to /api/applications,
  which stores the job in SQLite via SQLAlchemy.

  The tracker table at the bottom of the page shows all saved applications.
  Each row has a status dropdown (Saved → Applied → Phone Screen →
  Interview → Offer / Rejected). Changing the dropdown immediately PUTs
  the new status to /api/applications/{id}/status.

  The tracker persists across sessions via the local SQLite database.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  LLM BACKEND ROUTING & FAILOVER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Each agent declares a quality level (_quality = "high" or "fast").
  BackendRouter in backends/router.py applies this strategy:

    quality="high" (ResumeParserAgent, TailoringAgent)
      → Primary: AnthropicBackend (claude-sonnet-4-6)
        If the circuit breaker is OPEN: falls back to GroqBackend
        If Anthropic returns HTTP 401/402/429/502/503: trips the breaker
        and falls back to GroqBackend for that request

    quality="fast" (RoleInferenceAgent, JobMatchingAgent,
                    ResearchAgent, InterviewPrepAgent)
      → Direct: GroqBackend (llama-3.3-70b-versatile)
        Falls back to AnthropicBackend only if Groq is not configured

  Circuit Breaker states (backends/circuit_breaker.py):
    CLOSED    Normal — all requests go through Anthropic
    OPEN      Too many failures — all requests go to Groq
    HALF_OPEN After CIRCUIT_BREAKER_TIMEOUT seconds, one probe request
              is sent to Anthropic; success resets to CLOSED,
              failure keeps it OPEN

  Anthropic Prompt Caching:
    When cache_system=True (used by all agents), the system prompt is sent
    with cache_control=ephemeral. This caches the system prompt on
    Anthropic's servers for up to 5 minutes, reducing cost and latency
    for repeated calls with the same system prompt (e.g. scoring 100 jobs).


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SECURITY NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  - File uploads are validated by magic bytes (not file extension).
    Only PDF and DOCX pass through.
  - File size is capped at MAX_UPLOAD_BYTES (default 5 MB).
  - User-supplied job titles and locations are HTML-escaped before
    being sent to external APIs or returned in responses.
  - All API routes are rate-limited to 10 requests/minute per IP
    via slowapi.
  - CORS is restricted to localhost:8000 / 127.0.0.1:8000.
  - The .env file (API keys) is gitignored.
  - The SQLite database is stored in the data/ directory, which is
    also gitignored.
  - No authentication layer is included — this is designed for local
    personal use. Do not expose port 8000 to the public internet
    without adding authentication.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COST CONSIDERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Every resume upload triggers at minimum:
    - 1 Claude call for parsing (quality=high)
    - 1 Groq call for role inference (quality=fast, cheap/free)
    - Up to 100 Groq calls for scoring (quality=fast, cheap/free)

  Tailoring, research, and interview prep are on-demand (not automatic):
    - Tailoring: 1 Claude call per job (quality=high, the costliest call)
    - Research: 1 Groq call per job (quality=fast)
    - Interview prep: 1 Groq call per job (quality=fast)

  To minimise cost:
    - Set GROQ_API_KEY — Groq's free tier handles all fast-quality calls
      at no cost, leaving only parsing and tailoring on Anthropic
    - Set MAX_JOBS_PER_SOURCE lower (e.g. 10) to reduce scoring volume
    - Tab results are cached client-side; reopening the same job panel
      does not re-call the API


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  "At least one LLM backend must be configured"
    → ANTHROPIC_API_KEY is missing or blank in your .env file.

  "Invalid Anthropic API key"
    → Check ANTHROPIC_API_KEY in .env; ensure no trailing whitespace.

  "Anthropic credit balance too low"
    → Add credits at console.anthropic.com, or set GROQ_API_KEY so the
      circuit breaker can fall over to Groq automatically.

  "Only PDF and DOCX files are accepted"
    → The file failed MIME-type validation. Ensure the file is a real PDF
      or DOCX (not a renamed file or a corrupted download).

  "Could not extract text from the uploaded file"
    → The PDF may be a scanned image with no embedded text layer. Try a
      PDF with selectable text, or convert to DOCX first.

  Jobs section shows 0 results
    → Check that ADZUNA_APP_ID and ADZUNA_APP_KEY are set correctly.
      The other three sources (Remotive, The Muse, Arbeitnow) are free
      and require no credentials, so at least some jobs should appear.

  Uvicorn exits immediately on Windows
    → Run with: uvicorn main:app --reload
      Do not double-click main.py directly.
================================================================================
