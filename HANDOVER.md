AI Software Factory — Handover Document
> \*\*Purpose\*\*: Capture the complete context of this multi-VM AI software factory so that any future Claude session, or the owner (David), can pick up exactly where we left off without losing months of architectural decisions and battle-tested fixes.
>
> \*\*Last updated\*\*: May 5, 2026
> \*\*Owner\*\*: David Vanc (basic Linux skills, learning project mindset)
> \*\*Repo\*\*: https://github.com/davidvanc/ai-factory (private)
---
1. What This System Is
An autonomous multi-agent AI software factory running across 3 Proxmox VMs. Given a natural language description of a desired microservice, the system:
Plans the project architecture (Planner agent)
Optionally consults specialists (Scientific/Scraper consultants)
Generates code (Developer agent — Gemini Pro Latest)
Builds Docker images (Builder agent)
Tests via pytest + functional HTTP smoke tests
Has a Judge agent rate the result
Auto-pushes approved services to GitHub
Stores lessons learned in a central memory service
The system iterates with retries when tests fail, escalates to premium models on the last attempt, and detects "no progress" patterns to bail out gracefully.
---
2. Infrastructure
VMs
All on Proxmox, Ubuntu 22.04 Server, IPs reserved via DHCP on the router:
VM	Role	IP	Subnet	Gateway	Owner
Orchestrator	Pipeline coordinator, agents	192.168.128.197	192.168.128.247/23	192.168.128.1	user `david`
Worker	RQ worker that runs pipelines	192.168.129.82	192.168.128.247/23	192.168.128.1	user `david`
Storage	Memory service + Redis + Postgres	192.168.129.20	192.168.128.247/23	192.168.128.1	user `david`
A pre-existing Plex VM was left untouched.
Services on Storage VM
Service	Port	Purpose
Memory service (FastAPI + SQLite)	8765	Project history, lessons, port allocations
Redis	6379	RQ queue + rate limit backend (DB 0 and 1)
Postgres 18	5432	Persistent database (Docker container)
Critical Git Configuration
The Worker had `user.name` and `user.email` empty, causing silent push failures (the pipeline reported success but nothing was pushed). Fixed with:
```bash
git config --global user.name "AI Factory Worker"
git config --global user.email "worker@ai-factory.local"
```
This is essential — without it, you lose generated services.
SSH Keys
Both Orchestrator and Worker have their own SSH keys for GitHub:
Orchestrator: labeled `ai-factory-orchestrator`
Worker: labeled `Worker VM`
Both have read+write to the private repo `davidvanc/ai-factory`.
API Keys (in `.env` on both Orchestrator and Worker)
```
OPENROUTER\_API\_KEY=sk-or-...
FIRECRAWL\_API\_KEY=fc-...
POSTGRES\_PASSWORD=<chosen by user, contains @ which must be URL-encoded as %40>
DATABASE\_URL=postgresql://factory\_admin:<password-with-%40>@192.168.129.20:5432/factory\_main
DATABASE\_ENABLED=true
```
The `@` in the postgres password needs URL-encoding (`%40`) in `DATABASE\_URL` because the `@` is a URL parser delimiter.
---
3. Code Layout
Orchestrator: `/home/david/ai-factory/`
```
ai-factory/
├── main.py                         # Direct CLI entry (legacy, retry-loop logic still here)
├── submit.py                       # RQ enqueue helper
├── show\_log.py                     # Debug helper
├── diagnose.py                     # Debug helper
├── .env                            # Secrets (NOT in git)
├── venv/                           # Python virtualenv
│
├── src/
│   ├── llm/
│   │   ├── client.py               # LLMClient with streaming, prompt caching, idle timeout
│   │   ├── memory\_client.py        # HTTP client to Storage VM Memory service
│   │   └── json\_utils.py           # Robust JSON extraction with brace counting
│   │
│   ├── agents/
│   │   ├── planner.py              # Plans projects + Memory lessons + Domain Detector + Consultants
│   │   ├── developer.py            # Writes code, supports previous\_files feedback
│   │   ├── builder.py              # Writes Dockerfile, compose, README, tests config, ADR
│   │   ├── tester.py               # Build + pytest + runtime + functional smoke tests
│   │   ├── judge.py                # Calibrated pragmatic verdict
│   │   ├── functional\_tester.py    # Real HTTP testing for services, CLI testing for tools
│   │   ├── detector.py             # Hybrid keyword + LLM domain detection
│   │   ├── consultant\_scientific.py  # Gemini Pro for scientific knowledge
│   │   └── consultant\_scraper.py   # DeepSeek + Firecrawl, prefers public sites
│   │
│   ├── service\_template/           # NEW IN ITERATION 1+ — injected into every generated service
│   │   ├── \_\_init\_\_.py
│   │   ├── bootstrap.py            # create\_app() with all enterprise wiring
│   │   ├── settings.py             # Pydantic Settings (env-driven)
│   │   ├── logging\_config.py       # structlog JSON / console
│   │   ├── health.py               # /health, /ready
│   │   ├── metrics.py              # /metrics + middleware
│   │   ├── lifespan.py             # Startup/shutdown handlers
│   │   ├── auth.py                 # Bearer token verification
│   │   ├── rate\_limit.py           # slowapi + Redis
│   │   ├── resilience.py           # Size, timeout, security headers middleware
│   │   ├── database.py             # Async SQLAlchemy 2.0 (opt-in)
│   │   ├── alembic\_helper.py       # Alembic migration template generator
│   │   ├── adr\_template.py         # ADR markdown generator
│   │   ├── test\_fixtures.py        # Shared pytest fixtures
│   │   ├── contract\_tests.py       # Standard contract tests for every service
│   │   └── pyproject\_template.toml # pytest + coverage config
│   │
│   └── workflow/
│       └── pipeline.py             # The factory pipeline as a callable RQ function
│
├── output/                         # Generated services (also pushed to GitHub)
└── logs/                           # Per-run JSON logs
```
Worker: `/home/david/ai-factory-worker/`
Identical structure; obtained via `git clone`. Has its own venv with the same dependencies. The Worker pulls from GitHub and runs `rq worker`.
Storage: `/home/david/memory-service/`
```
memory-service/
├── server.py                       # FastAPI service
├── factory.db                      # SQLite database
└── memory-service.service          # systemd unit
```
Started as a systemd service called `memory-service`.
Storage: `/home/david/postgres/`
```
postgres/
├── docker-compose.yml              # Postgres 18 container
└── .env                            # POSTGRES\_PASSWORD
```
Volume mount is `/var/lib/postgresql` (NOT `/var/lib/postgresql/data`) — Postgres 18 changed the layout.
---
4. The Pipeline Flow
```
User runs: python submit.py "Make a service that does X"
     │
     ▼
Job enqueued to Redis at 192.168.129.20:6379, queue "factory"
     │
     ▼
Worker picks up job, calls run\_factory\_pipeline(task)
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 1. PLANNER (Claude Opus 4.7)                           │
│    - Domain Detector classifies task                   │
│    - Calls Scientific or Scraper Consultant if needed  │
│    - Pulls relevant lessons from Memory                │
│    - Outputs: project\_name, structure, endpoints,      │
│      tests list, requirements, needs\_database          │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 2. DEVELOPER (Gemini Pro Latest by default)            │
│    - Writes all code as JSON {files: \[...]}            │
│    - Uses service\_template imports                     │
│    - Premium escalation to Claude Opus 4.7 on last try │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 3. BUILDER (deterministic, no LLM)                     │
│    - Writes developer files (skips Dockerfile, etc.)   │
│    - Copies service\_template into src/                 │
│    - Writes Dockerfile, docker-compose.yml             │
│    - Writes README with curl examples per endpoint     │
│    - Writes pyproject.toml with coverage gate          │
│    - Writes ADR.md                                     │
│    - Writes .gitignore, .dockerignore                  │
│    - Allocates unique port from Memory service         │
└────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 4. TESTER (deepseek-v4-flash)                          │
│    - Stage 1: docker build                             │
│    - Stage 2: pytest in container (-p no:cacheprovider)│
│    - Stage 3: runtime startup test                     │
│    - Stage 4: functional smoke tests (HTTP for service)│
└────────────────────────────────────────────────────────┘
     │
     ▼
If tests fail: feedback → Developer → Builder → Tester (max 6 attempts)
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 5. JUDGE (Claude Sonnet 4.6)                           │
│    - Reviews code, README, tests, output               │
│    - Verdict: APPROVED or REJECTED with reasons        │
└────────────────────────────────────────────────────────┘
     │
     ▼
If REJECTED: feedback → Developer (max 3 judge retries)
     │
     ▼
┌────────────────────────────────────────────────────────┐
│ 6. GIT PUSH + MEMORY UPDATE                            │
│    - \_push\_to\_git with retry-loop and fail-loud        │
│    - MemoryClient.add\_project records the run          │
└────────────────────────────────────────────────────────┘
```
Retry-Loop Constants (in `pipeline.py` and `main.py`)
Constant	Value	Meaning
`MAX\_TESTER\_ATTEMPTS`	6	Max retries while tests fail
`MAX\_JUDGE\_ATTEMPTS`	3	Max retries to get APPROVED
`NO\_PROGRESS\_THRESHOLD`	2	Bail out if passing test count doesn't increase 2x in a row
Premium model escalation happens on the final attempt.
---
5. Model Routing
In `src/llm/client.py`:
```python
MODEL\_ROUTES = {
    "planner":               "anthropic/claude-opus-4-7",
    "developer":             "\~google/gemini-pro-latest",
    "developer\_premium":     "anthropic/claude-opus-4-7",
    "builder":               "deepseek/deepseek-v4-flash",
    "tester":                "deepseek/deepseek-v4-flash",
    "judge":                 "anthropic/claude-sonnet-4-6",
    "consultant\_scientific": "\~google/gemini-pro-latest",
}
```
Why these models?
Opus 4.7 for Planner: Best architectural reasoning, structured JSON output
Gemini Pro Latest for Developer: Tested DeepSeek V4 Pro first but had degeneration loops (the model would repeat single words forever). Gemini is stable, supports 1M token input, and produces good code. The `\~` prefix means "always latest version".
Flash for Builder/Tester: They barely use the LLM — simple tasks
Sonnet 4.6 for Judge: Good reasoning at lower cost than Opus
Premium escalation: Last attempt uses Opus to break out of failure patterns
Caching
OpenRouter supports prompt caching for `anthropic/`, `google/` and `\~google/` models. Implemented in `client.py`:
```python
if supports\_caching and len(prompt) > 1024:
    cache\_split = max(0, len(prompt) - 200)
    messages = \[{
        "role": "user",
        "content": \[
            {"type": "text", "text": prompt\[:cache\_split], "cache\_control": {"type": "ephemeral"}},
            {"type": "text", "text": prompt\[cache\_split:]}
        ]
    }]
```
`max\_tokens` capped at 32,000. Idle timeout of 90s aborts stuck streams.
---
6. Major Lessons Hard-Earned
6.1 The 4 Times f-strings Bit Us
Python f-strings interpret `:` inside `{...}` as a format specifier. Dict literals like `{"key": "value"}` inside an f-string explode with `Invalid format specifier`.
Fixes applied in prompt strings:
Use `{{...}}` for literal braces in the JSON template strings
Use `dict(key=value)` instead of `{"key": "value"}` in example code
This bit us 4 separate times. If you see "Invalid format specifier" — search for dict literals in f-strings.
6.2 The Silent Git Push Failure
The Worker reported `\[git] X succesvol gepusht (poging 1)` but nothing reached GitHub. Root cause: `user.name` and `user.email` were empty on the Worker (`git commit` silently failed on identity check, but the wrapper code didn't check exit code).
Fixed by:
Setting global git config (see infrastructure section)
Making `\_push\_to\_git` in `pipeline.py` fail-loud with explicit checks at each step
6.3 Public Sites > APIs (Scraper Consultant)
The Scraper Consultant initially loved suggesting API endpoints. These often:
Required API keys we didn't have
Were deprecated (OpenAQ V2 returned `410 Gone`)
Had complex parameter requirements
Fixed by rewriting the prompt to prefer public websites like `kmi.be`, `meteo.be`, `wikipedia.org` over APIs. This isn't perfect for all use cases (David paused this work for later), but it's much more robust.
6.4 The Port Conflict Saga
Pipeline allocated unique ports per service via Memory's port allocator (8001, 8002, 8003, ...). But:
Planner sometimes hardcoded `:8000` in `curl\_example` strings
README would show wrong port
Functional Tester occasionally tested wrong port due to caching
Builder now normalizes hardcoded ports via regex `:\\d{4,5}` → real allocated port
Allocations stored in Storage VM SQLite via `/ports/allocate` endpoint, idempotent (same project name = same port).
6.5 LLM Degeneration (the "response. response. response..." Loop)
DeepSeek V4 Pro entered an infinite repetition loop generating only the word "response". Idle timeout (90s) didn't catch it because data WAS arriving — just garbage.
Fixed by:
Switched Developer to Gemini Pro Latest
Added `max\_tokens: 32000` cap as safety net
6.6 The Functional Tester Race Condition
Container started → `\_wait\_for\_port` returned True → curl returned `HTTP 000`. Cause: TCP socket connect succeeded against Docker's port forwarder before uvicorn was actually listening.
Fixed by switching `\_wait\_for\_port` from `socket.create\_connection` to `urllib.request.urlopen` so we test for real HTTP response (404/405 OK = service alive but path missing).
6.7 Database Tests Were a Tar Pit
Iteration 4 added Postgres support. The DB module worked great in production, but tests were a nightmare:
`Pydantic Settings` is a singleton imported at module load — `monkeypatch.setenv` doesn't affect it
Async fixtures + pytest-asyncio + SQLAlchemy interaction is brittle
Tests tried to connect to localhost:5432 in containers without Postgres
Coverage gate kept failing because routes.py couldn't be tested
Final pragmatic decision: defaulted Planner to `needs\_database=false` and accept that DB-services are written by hand. The DB infrastructure stays in the template for manual use.
6.8 Read-only + Non-root Container Issues
Iteration 5 introduced multi-stage Dockerfile with non-root user (uid 1001) and `read\_only: true` in docker-compose.prod.yml. Then:
pytest cache wanted to write to `/app/.pytest\_cache` → permission denied
Coverage data file wanted to write to `/app/.coverage\*` → permission denied
Tests excluded from image via `.dockerignore tests/` → 0 tests collected
Partial fixes applied:
`pytest -p no:cacheprovider` skips cache
Removed `tests/` from `.dockerignore` (but should be excluded from production builds via build flag)
Coverage write issue: NOT YET RESOLVED at time of handover (see PROJECT_STATE.md)
---
7. Architectural Decisions (ADRs)
ADR-1: Microservices by Default
Every generated project is a FastAPI service unless explicitly stateless+CLI. This is enforced in the Planner prompt.
Rationale: A service with HTTP endpoints is more useful as a building block than a CLI tool. David wants to compose complex programs from microservices.
ADR-2: Service Template Injection
Instead of teaching the Developer to write all the boilerplate (logging, health checks, metrics), the Builder copies a `service\_template/` directory into every generated service. The Developer only writes business logic and uses imports from the template.
Rationale: Consistent quality across all services, fewer LLM tokens spent on boilerplate, easier to upgrade all services at once.
ADR-3: Async Python with FastAPI
All services are async. Database calls use SQLAlchemy 2.0 async API with `asyncpg`. Tests use SQLite via `aiosqlite` for speed.
Rationale: FastAPI is async-first; sync would waste 90% of its concurrency benefit.
ADR-4: 80% Coverage Gate
Pytest fails if coverage is below 80% (configured in `pyproject\_template.toml`). Coverage is measured on `src/logic.py`, `src/schemas.py`, `src/routes.py` but excludes `src/service\_template/`, `src/main.py`, `src/database.py`, `src/models.py`.
Rationale: Force the Developer to write real tests; exclude infrastructure that doesn't need direct testing.
ADR-5: 12-Factor Configuration
All settings via environment variables with Pydantic validation. No infrastructure addresses hardcoded in defaults (Redis URL defaults to `redis://localhost:6379/1`, must be overridden in production).
Rationale: Same image runs in dev, staging, prod — only env vars change.
ADR-6: Domain Consultants
Before the Planner runs, a Domain Detector classifies the task (`scientific`, `scraping`, `general`). Detected domains call specialist consultants:
Scientific Consultant (Gemini Pro): provides domain knowledge from training (formulas, terminology, edge cases)
Scraper Consultant (DeepSeek + Firecrawl): provides live web data when training data isn't enough
Rationale: A Developer can write good code without knowing what BMI is, but the Plan needs that knowledge so tests and structure are correct.
ADR-7: Fail-Loud Git Push
The original `\_push\_to\_git` reported success even when nothing was pushed. Now:
Pre-checks `git config user.name` and `user.email`
Checks exit code at every git step
Raises exception when retries are exhausted
Rationale: Silent failures are the worst kind. Better to crash visibly.
ADR-8: Microservices Database is Opt-In
Default `needs\_database=false`. The Developer and Builder don't generate DB code unless explicitly requested.
Rationale: Tests with async DB + Pydantic Settings + pytest-asyncio + SQLAlchemy is too brittle for autonomous generation. Real teams write schema by hand for good reasons.
---
8. Token Usage and Costs
Approximate costs from this entire session, totaling ~25 hours of agent runs:
Model	Approx cost
Claude Opus 4.7 (Planner + Developer Premium)	~$3.50
Gemini Pro Latest (Developer + Scientific Consultant)	~$1.20
Claude Sonnet 4.6 (Judge)	~$0.80
DeepSeek V4 Flash (Builder, Tester)	~$0.20
Firecrawl (Scraper)	Free tier (500 credits)
Total	~$5.70
Caching reduced retry costs significantly.
---
9. Known Working Use Cases (8+ services delivered)
These were generated successfully end-to-end and pushed to GitHub:
Service	Type	Note
`statistics\_tool`	CLI	First-poging success
`password\_generator\_service`	Service	Iteration 3 milestone, 97% test coverage
`hex\_color\_converter`	Service	Iteration 1 milestone — full enterprise template validated
`morse\_converter`	CLI	After 2 retries
`palindroom\_checker`	CLI	After 2 retries
`time\_api`	Service	Original simple service
`json\_stats\_cli`	CLI	Original
`text\_analyzer\_service`	Service	Pre-template version
`date\_format\_converter`	Service	First-poging with port fixes
`getal\_naar\_nl\_tekst`	Service	Dutch number-to-text (101 → "honderdeen", correct)
`french\_number\_converter`	Service	French numbers (80 → "quatre-vingts")
`case\_converter\_service`	Service	Iteration 1 polish complete (correct service_name in logs)
`uuid\_generator\_service`	Service	Iteration 2 milestone — security headers visible
Failed Cases (Educational)
Attempted	Why it failed
`be\_air\_quality\_health`	LLM hallucinated API endpoints; OpenAQ V2 was 410 Gone
`be\_air\_quality\_monitor`	Same issue
`uv\_index\_scraper`	Geocoding bug in generated code; OpenWeatherMap requires key
`customer\_service` (DB)	DB tests too brittle; iteration 4 paused
`calculator\_service`	Iteration 5 broken — read-only filesystem + non-root user
---
10. Critical Commands Reference
Start RQ Worker
```bash
# On Worker VM
cd \~/ai-factory-worker
source venv/bin/activate
rq worker --url redis://192.168.129.20:6379 factory
```
Submit a Job
```bash
# On Orchestrator
cd \~/ai-factory
source venv/bin/activate
python submit.py "Make a service that does X"
```
Inspect Memory
```bash
# Stats
curl -s http://192.168.129.20:8765/stats | python3 -m json.tool

# All allocated ports
curl -s http://192.168.129.20:8765/ports | python3 -m json.tool

# Recent projects
curl -s http://192.168.129.20:8765/projects?limit=10 | python3 -m json.tool
```
Test a Generated Service
```bash
# On Worker
docker run -d --rm --name test-svc -p PORT:PORT ai-factory/SERVICE\_NAME:test
sleep 4
curl -s http://localhost:PORT/health
docker stop test-svc
```
Inspect Last Run Log
```bash
ls -t \~/ai-factory-worker/logs/job\_\*.json | head -1 | xargs cat | python3 -m json.tool
```
Check Postgres
```bash
# From Storage VM
docker exec -it postgres psql -U factory\_admin -d factory\_main

# From any VM
psql -h 192.168.129.20 -U factory\_admin -d factory\_main -c "SELECT version();"
```
---
11. The 5-Iteration Enterprise Path
We agreed on a 5-iteration plan to reach "technical enterprise-grade":
Iteration	What	Status
1	Skeleton + Configuration + Observability	✅ COMPLETE
2	Security + Resilience	✅ COMPLETE
3	Testing + Documentation	✅ COMPLETE
4	Postgres database integration	⚠️ INFRASTRUCTURE READY, AUTOMATION PAUSED
5	Deployment + CI/CD	❌ INCOMPLETE — see PROJECT_STATE.md
David was clear from the start that he aims for technical enterprise-grade (all 8 dimensions of a productie-grade service achievable by one person), NOT certifiable enterprise (which requires SOC 2, compliance officer, legal team, etc).
---
12. What Each Future Session Should Know
Personal context
David is a learning-oriented user with basic Linux skills. He works through PuTTY with multiple sessions open. He thinks like an architect and asks excellent design questions. He values:
Honest answers about what works vs what doesn't
Trade-off explanations before recommendations
Pragmatic decisions over perfectionism
Working systems over impressive demos
Communication style
Dutch for explanations and discussions
English for code, commit messages, file contents
Concise responses — David doesn't want walls of text
Always one logical step at a time
Check understanding before making big changes
When something fails, diagnose first, fix later
Workflow rules established
Always commit and push to GitHub — never sync via direct file copy between VMs
Work on Orchestrator, push, pull on Worker
When in doubt about syntax errors, send the full corrected file rather than incremental nano edits
Stop and pause when David says he's lost; don't push forward
Acknowledge mistakes openly; don't pretend things are working when they're not
What NOT to suggest
Don't push for SOC 2 / compliance work (David is realistic about scope)
Don't promote DeepSeek V4 Pro for Developer (degeneration issues)
Don't add hardcoded IPs in default configs
Don't build database services automatically (write by hand)
Don't suggest scrapers for unstable APIs
---
13. Where to Pick Up
Current state: Iteration 5 is broken. Read `PROJECT\_STATE.md` for exact technical state and `README.md` for a runbook on how to use the system today.
Recommended next step: Roll back the iteration 5 commits to the iteration 3 stable state (last known working = `password\_generator\_service` from iteration 3). Then redo iteration 5 in much smaller steps with full validation between each.
```bash
# To find the last known-good commit
cd \~/ai-factory
git log --oneline | grep -A1 "Iteration 3"
```
The system at iteration 3 generates production-quality stateless microservices in 2-4 minutes per service. That's already extremely valuable. Iteration 5's deployment polish is nice-to-have, not blocking.
---
End of Handover
If you are a future Claude session reading this: please don't repeat the architectural mistakes. Read all three documents (`HANDOVER.md`, `PROJECT\_STATE.md`, `README.md`) before suggesting any changes. David has invested significant time and energy; treat the system with care.
