Project State
> \*\*Last updated\*\*: May 8, 2026
>
> Snapshot of every component's current state. Read this before making changes.

### Bekende issue (2026-05-08)

- Bij retry-attempts (>2) met grote previous_files kan de Developer-response truncated raken
  (LLM output wordt afgekapt onder context-druk), wat resulteert in een ValueError uit extract_json.
  Geobserveerd op een todo-list run met 3+ attempts. Niet structureel — komt niet voor bij
  simpele tasks of attempts 1-2.
- Mogelijke mitigaties (toekomstig): previous_files snijden bij retry-attempts (alleen de files
  die in de feedback genoemd worden), of extract_json tolerant maken voor truncated JSON.

## 2026-05-08 Sessie samenvatting

### Bereikt

- **Per-attempt code snapshots**: `logs/snapshots/{job_id}/attempt_N/files.json` per attempt geschreven door `_snapshot_attempt_files` in pipeline.py. Maakt diff-based lesson-extractie mogelijk.
- **Failing tests in log**: pytest-failures per attempt geparsed via `_extract_test_names` (ANSI-tolerant) en opgenomen als `failing_tests` veld. Functional smoke failures blijven in `failure_context.issues`.
- **Cumulative failure history (Fix A)**: pipeline houdt `failure_history` bij door de hele run, geeft die door aan de Developer prompt als `📜 GESCHIEDENIS` block met cross-attempt framing ("ALLE issues tegelijkertijd oplossen, geen hack-cyclus"). Latent geïmplementeerd — niet gevalideerd onder echte multi-attempt condities omdat die zeldzaam werden na de hieronder genoemde fix.
- **Lessons-extractor v1**: standalone script `scripts/extract_lessons.py`. Eligibility-checks (success + final_attempt ≥ 2 + snapshots aanwezig + APPROVED gevonden), snapshot-loading, prompt-assembly, LLM-aanroep via `role="planner"` (Opus). Refusal-paden gevalideerd. Refusal-discipline werkt: extractor weigert lessen te bouwen op test-gaming "fixes" die door Judge geslipt zijn — fungeert als second-opinion op de Judge.
- **Key fix — functional_tester**: ontdekt dat `request_example` alleen werd gebruikt voor POST/PUT/PATCH (als body), niet voor GET (als query string). Resultaat: GET endpoints werden zonder parameters getest, wat de Developer dwong tot hardcoded fallbacks om "tester pass" te halen. De "approved" code bevatte daardoor structureel test-gaming hacks die de Judge inconsistent ving. Fix: `urlencode(request_example)` toegevoegd voor GET requests in `_run_service_tests`. Twee opeenvolgende 1-attempt successes na de fix (hex_color_converter + één andere taak).

### Empirische vondst

Het regression-loop patroon (tester-fail → hack → judge-fail → tester-fail) was **niet primair een Developer-prompt probleem**. Het was een gevolg van een verkeerd ontworpen test-vraag: een endpoint zonder verplichte parameter werd getest met `expected: 2xx` wat alleen via een hardcoded default haalbaar is. De Developer reageerde rationeel op een onmogelijke vraag. Conclusie: bij rare loops eerst checken of de tester een eerlijke vraag stelt voordat aan prompts wordt getrokken.

### Status updates

| Component | Was | Nu |
|---|---|---|
| Per-attempt code snapshots | ❌ Missing | ✅ `logs/snapshots/{job_id}/attempt_N/files.json` |
| Failing tests in log | ❌ Missing | ✅ `failing_tests` veld per attempt |
| Cumulative failure history | ❌ Niet | ✅ Geïmplementeerd, latent (n=0 echte validatie) |
| Functional tester realisme | ⚠️ alleen POST/PUT/PATCH body | ✅ ook GET query string uit request_example |
| Lessons auto-extractie | ❌ Niet | 🟡 Script klaar, niet gepipeline-d, wacht op data |
| Test-gaming detection | Alleen via Judge (inconsistent) | ✅ ook via extractor's refusal-discipline |

### Open

- Validatie-runs over diverse task-types: hoe robuust is 1-attempt success buiten simpele kleur-conversie?
- Eerste echte lesson-extractie zodra multi-attempt success post-fix optreedt
- Lessons-extractor pipeline-integratie (auto-call post-success) — pas zinvol als handmatige extractie iets oplevert
- Functional tester uitbreiden met negatieve scenarios (4xx paden expliciet testen)
- Cumulative history blijft onvalidated tot complexere taken weer multi-attempt nodig hebben
- Domain detection few-shot (future.txt): niet gestart
- Schema-first DB services (future.txt): geparkeerd

### Aanbevolen vervolg

1. Validatie-runs over 3-5 verschillende task-types (stateful, multi-endpoint, scraper, externe validatie). Identificeer welke complexiteit nog multi-attempt nodig heeft.
2. Bij eerste multi-attempt success: extractor handmatig draaien, beoordelen of gegenereerde lesson zinvol is.
3. Bij positief resultaat van (2): pipeline-integratie. Niet eerder — geen punt om injectie te bouwen voor een lege DB.
---

## 2026-05-07 Sessie samenvatting

### Bereikt

- **Rollback**: main staat op stable iter3-base (`7a4d09e` ancestry). Iter5 broken commits gearchiveerd als `main-archive-2026-05-06`. Drie sanity-tests bevestigen werking.
- **Phase 5A — HEALTHCHECK**: alle gegenereerde services hebben nu een Python-based HEALTHCHECK directive. Geverifieerd op `md5_hash_service` (`Up X seconds (healthy)`).
- **Baseline metrics**: `scripts/factory_baseline.py` aggregeert pipeline-statistieken uit job logs. Eerste snapshot in `docs/baseline-2026-05-06.md`. Pre-fix cijfers: 51.9% success, 22.2% first-attempt APPROVED, 0% premium usage waargenomen.
- **Pipeline failure logging**: `failure_context` per attempt (issues, test_output_excerpt, failing_criteria), `traceback` + `error_type` + `error_during_attempt` in top-level errors. Alle failures vanaf nu gestructureerd vastgelegd.
- **Developer prompt — incremental retry**: preservation-rules vooraan, visuele markers, onderscheid tester-fail vs judge-reject. Empirisch gevalideerd op twee tasks: Roman numerals (was 7-att fail → werd 2-att success), ISBN validator (success).
- **build_feedback polish**: parset functional smoke JSON om concrete scenario-failures in `issues` te zetten.
- **Incremental log persistence**: log wordt nu na elke attempt naar disk geschreven, live visibility tijdens runs mogelijk.

### Empirische vondst

De retry-loop was **regeneratief, niet incrementeel**. Empirisch bewijs: Roman numerals run pre-fix had attempt_4 met passing tests, daarna attempts 5-7 weer falend — de Developer brak werkende code terwijl hij Judge-feedback adresseerde. De prompt-fix lijkt dit op te lossen (n=2 datapunten).

### Status updates

| Component | Was | Nu |
|---|---|---|
| RQ pipeline (iter5) | ❌ Broken | ✅ Teruggerold, Phase 5A incrementeel werkend |
| Per-attempt failure logging | ❌ Missing | ✅ Geïmplementeerd |
| Live visibility tijdens runs | ❌ Geen | ✅ Incrementeel log persist |
| Retry-mechanisme | Regeneratief | Edits-preserving (prompt-level) |
| Failure data structuur | Alleen pass/fail | Issues, test output, criteria |

### Open

- Lessons auto-extractie: nog niet gestart, maar nu haalbaar dankzij gestructureerde `failure_context`
- Phase 5B (non-root user): bewust niet gedaan
- Domain detection few-shot: niet gedaan
- Schema-first DB services: geparkeerd
- Robuustheid prompt-fix: nog n=2 validatie-runs, te weinig voor sterke claims

### Aanbevolen vervolg (toekomstige sessies)

1. Meer validatie-runs over diverse task-types (data parsing, API services, file processing) om robuustheid prompt-fix te bevestigen
2. Lessons auto-extractie ontwerp + implementatie nu de input-data klopt
3. Re-baseline na N nieuwe runs om effect prompt-fix kwantitatief te meten
---
Quick Status
Component	State	Last verified
Orchestrator VM (192.168.128.197)	✅ Working	2026-05-05
Worker VM (192.168.129.82)	✅ Working	2026-05-05
Storage VM (192.168.129.20)	✅ Working	2026-05-05
Memory service (port 8765)	✅ Working	2026-05-05
Redis (port 6379)	✅ Working	2026-05-05
Postgres 18 (port 5432)	✅ Working	2026-05-04
RQ pipeline (Iterations 1-3)	✅ Last working state	2026-05-04
RQ pipeline (Iteration 5)	❌ Broken	2026-05-05
Auto-push to GitHub	✅ Working	2026-05-04
Memory + lessons	⚠️ Partial — projects yes, lessons not auto-extracted	2026-05-04
---
Working Components
Orchestrator VM
Python 3.12 venv at `\~/ai-factory/venv/`
All factory dependencies installed (fastapi, uvicorn, structlog, sqlalchemy, etc.)
Git config: `user.name="David Vanc"`, push works
`.env` has all keys (OpenRouter, Firecrawl, Postgres password, DATABASE_URL)
Can run `python submit.py "..."` to enqueue jobs
Worker VM
Python 3.12 venv at `\~/ai-factory-worker/venv/`
Same dependencies as Orchestrator
Git config: `user.name="AI Factory Worker"`, `user.email="worker@ai-factory.local"`
SSH key registered with GitHub
RQ worker can be started with `rq worker --url redis://192.168.129.20:6379 factory`
Storage VM
Memory Service (systemd)
File: `/home/david/memory-service/server.py`
SQLite database: `/home/david/memory-service/factory.db`
Tables:
`projects` — every run logged
`lessons` — learning extraction (not auto-populated yet)
`port\_allocations` — incremental from 8001
Endpoints all functional:
`GET /stats`
`GET /projects?limit=N`
`GET /lessons/relevant?task=...`
`POST /ports/allocate?project\_name=X`
`GET /ports`
Redis
Docker container or native install (verify with `docker ps | grep redis` or `systemctl status redis`)
Port 6379, no auth
Used by RQ for queue (DB 0) and slowapi for rate limiting (DB 1)
Postgres 18
Docker container at `\~/postgres/`
Volume mount: `/var/lib/postgresql` (NOT `/data` — Postgres 18 changed layout)
Admin user: `factory\_admin`
Default DB: `factory\_main`
Password: in `\~/postgres/.env`
Reachable from Orchestrator and Worker (verified)
---
Working Pipeline (Iteration 3 State)
When the system was last fully working (commit prior to Iteration 4):
Pipeline produces services with:
✅ FastAPI with Pydantic Settings
✅ Structured JSON logging via structlog with request IDs
✅ `/health`, `/ready`, `/metrics`, `/docs`, `/openapi.json` endpoints
✅ Request ID middleware
✅ Bearer token auth (opt-in, default off)
✅ Rate limiting via slowapi+Redis (opt-in)
✅ Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
✅ CORS configurable via env
✅ Request body size limit, request timeout
✅ 80% test coverage gate
✅ Standard contract tests (6 tests verify health/ready/metrics/headers/openapi)
✅ ADR.md generated per service
✅ pyproject.toml with pytest+coverage config
✅ Dockerfile (single-stage, no security hardening yet)
✅ docker-compose.yml
✅ README.md with curl examples
✅ Auto git push when APPROVED
Verified examples that work end-to-end:
```bash
# 1. uuid\_generator\_service (iteration 2)
docker run -d --rm --name uuid -p 8012:8012 ai-factory/uuid\_generator\_service:test
sleep 4
curl -X POST http://localhost:8012/generate
# Returns: {"uuid": "..."}
docker stop uuid

# 2. password\_generator\_service (iteration 3 — best example)
docker run -d --rm --name pwd -p 8013:8013 ai-factory/password\_generator\_service:test
sleep 4
curl -X POST http://localhost:8013/generate -H "Content-Type: application/json" \\
  -d '{"length": 16, "include\_digits": true, "include\_uppercase": true, "include\_lowercase": true, "include\_symbols": true}'
# Returns: {"password": ")tPH,8Ep?M?:(3>z", "length": 16}
docker stop pwd

# 3. case\_converter\_service (iteration 1 polish — full template validation)
docker run -d --rm --name cct -p 8011:8011 ai-factory/case\_converter\_service:test
sleep 4
curl -X POST http://localhost:8011/convert/all -H "Content-Type: application/json" \\
  -d '{"text": "hello world example"}'
# Returns: {"original": "hello world example", "upper": "HELLO WORLD EXAMPLE", ...}
docker stop cct
```
---
Broken / Unfinished
Iteration 4: Database Integration
Status: Infrastructure is in place but pipeline doesn't generate DB-services automatically.
What works:
Postgres 18 running on Storage VM, reachable cross-VM
`src/service\_template/database.py` async SQLAlchemy module
Settings has DATABASE_* fields
`init\_database()`, `close\_database()`, `database\_health\_check()` work
Alembic helper `generate\_alembic\_setup()` exists
Bootstrap auto-adds DB readiness check to `/ready`
What doesn't work:
Generating a service with `needs\_database=true` triggers test failures
Pydantic Settings singleton + monkeypatch interaction is brittle
Test fixtures expect SQLite for in-memory but settings stay configured for Postgres
Coverage gate fails because `routes.py` (which uses `get\_db`) can't be tested without DB
Resolution chosen: Default Planner to `needs\_database=false`. Build DB services by hand using the template infrastructure.
Iteration 5: Deployment + CI/CD
Status: 4 patches deep, last 2 days of work, NOT successfully tested end-to-end.
What was added:
Multi-stage Dockerfile in Builder (builder stage + runtime stage)
Non-root user (uid 1001) in runtime stage
HEALTHCHECK in Dockerfile
`.dockerignore` (later partially reverted)
`docker-compose.prod.yml` with resource limits, read_only filesystem, no-new-privileges
GitHub Actions workflow per service (`.github/workflows/ci.yml`)
Bugs introduced (in order of discovery):
`.dockerignore` excluded `tests/` → pytest in image found 0 tests
Status: ⚠️ PATCHED but not verified end-to-end
Fix applied: removed `tests/` from `.dockerignore`
Non-root + writable /app conflict → `pytest --cov` can't write `.coverage` data file
Error: `Couldn't use data file '/app/.coverage.b2b37938b897.pid1.XKwmyGtx': unable to open database file`
Status: ❌ NOT FIXED — last failing run was `calculator\_service` on 2026-05-05
pytest cache write to `/app/.pytest\_cache` → permission denied
Status: ✅ Fixed with `pytest -p no:cacheprovider`
Recommendation: Roll back the multi-stage Dockerfile changes and the docker-compose.prod.yml, return to iteration 3 stable state, then redo iteration 5 piece by piece with verification.
```bash
# Rollback strategy
cd \~/ai-factory
git log --oneline | head -20
# Find the commit before "Iteration 5" started
git revert <commit-hash> --no-edit  # for each iteration 5 commit, in reverse order
```
Or alternative: keep the multi-stage build but make `appuser` writable on `/app/.coverage` and `/app/.pytest\_cache` only.
---
Files That Need Manual Cleanup Before Continuing
File	Issue
`\~/ai-factory-worker/output/calculator\_service/`	Last broken attempt — delete
`\~/ai-factory-worker/output/customer\_service/`	DB attempt — delete (or keep as reference)
`output/` in git	Several iteration 5 broken services may be there
```bash
# Suggested cleanup before continuing
cd \~/ai-factory-worker
rm -rf output/calculator\_service output/customer\_service

# On Orchestrator after rollback
git pull
```
---
Outstanding Improvements (Future Work)
High value
Auto-extract lessons from failed runs — Memory has the table but nothing populates it from the Judge feedback or test failures. A script could parse failed runs and create lesson entries.
Better Domain Detection — Currently uses keyword matching with LLM fallback. The LLM occasionally classifies BMI calculator as "general" instead of "scientific". A few-shot examples in the prompt would help.
Real Scraper Consultant — David paused this after the public-sites prompt change. Could be re-attempted with structured data extraction from known-good sites (Wikipedia, government endpoints).
Schema-First Database Services — User defines schema as YAML/JSON, system generates models + migrations + endpoints. Skips the LLM-writes-SQLAlchemy nightmare.
Service-to-service mesh — When David's microservices need to call each other, we need a shared HTTP client with retries, circuit breakers, mutual TLS or shared API tokens.
Nice to have
Health check should NOT be exempt from auth (currently always public). Add `health\_auth\_required` setting.
OpenAPI examples in `request\_example` should auto-validate against the actual Pydantic models.
Per-service GitHub Actions could push to a real registry (currently commented out in workflow).
Structured commit messages — "feat(service-name)" prefix per generated service.
Multi-environment configs — `dev.env`, `staging.env`, `prod.env` templates per service.
Low value / experimental
Generate Kubernetes manifests alongside docker-compose
Helm chart per service
Distributed tracing with OpenTelemetry
Service registration/discovery via Consul or etcd
Web dashboard for the factory (instead of just CLI)
---
Resource Usage
VM resources (estimated)
VM	CPU	RAM	Disk
Orchestrator	2 cores	2 GB	~5 GB used
Worker	2 cores	4 GB	~10 GB used (Docker images add up)
Storage	1 core	1 GB	~3 GB used
Recommended cleanup commands when disk fills
```bash
# Worker — most disk-hungry
docker system prune -a --volumes  # NUKES all unused Docker things
docker images | grep "ai-factory" | awk '{print $3}' | xargs docker rmi  # Remove all factory images
```
---
Where Important Artifacts Live
Where	What
GitHub `davidvanc/ai-factory`	Source code + generated services in `output/`
`\~/ai-factory-worker/logs/job\_\*.json`	Per-run pipeline logs (Worker)
`\~/ai-factory/logs/run\_\*.json`	Older run logs (Orchestrator, pre-RQ era)
`192.168.129.20:8765/stats`	Memory service stats
Storage VM `factory.db`	SQLite with all project history
Postgres `factory\_main`	Empty (no DB-services run yet)
---
Summary
The good: 13 services successfully generated, multi-VM distributed system works, enterprise-grade observability and security baked in, ~$5.70 spent for ~25 hours of agent runs.
The not-so-good: Iteration 4 (database) and 5 (deployment) hit fundamental complexity. We have the building blocks but lost autonomous generation in the last few sessions.
The path forward: Roll back to iteration 3, re-implement iteration 5 carefully with smaller steps and val
