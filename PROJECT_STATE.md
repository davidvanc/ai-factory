markdown# Project State

> **Last updated**: May 9, 2026
> **Status**: Stable post-validation milestone — 6/6 task-types first-attempt APPROVED
> **Branchable from**: tag `v2026-05-09-validated`

> **Architectuur-update juni 2026**: van 3 VM's naar 1 machine. Redis/RQ-queue en de HTTP Memory-service zijn verwijderd; memory is nu lokale SQLite (`data/factory.db`), `submit.py` is weg en `main.py` draait de pipeline synchroon. Zie de banner bovenaan `HANDOVER.md`.

## Quick Status

| Component | State |
|---|---|
| Lokale orchestrator (`python main.py`) | ✅ Working — één proces, geen VM's |
| Memory (SQLite, `data/factory.db`) | ✅ Working — vervangt de HTTP Memory-service |
| Postgres 18 (on-demand via docker compose) | ✅ Working (ongebruikt door pipeline by design) |
| Pipeline | ✅ Working — first-attempt approved op typische CRUD + computatie |
| Auto-push to GitHub | ✅ Working |
| Functional tester | ✅ Plan-driven, stateful, regex path-param injectie |
| Test-isolation in gegenereerde services | ✅ Belt-and-suspenders (conftest + test files) |
| Lessons-extractor | 🟡 Manual mode getest, prompt refinement nodig voor pipeline-integratie |
| Cumulative failure history | ✅ Gevalideerd via library lending run |
| Schema-first DB services | ❌ Bestaat niet — TODO #2 |

## Recente milestone — 2026-05-09

Twee structurele bugs gefixt, twee features gerefactord, één feature voor 't eerst onder echte condities gevalideerd.

### Bereikt

1. **Truncation-fix in pipeline.py**: `previous_files` wordt bij retry-attempts gesliced naar (a) auto-include set [test files, conftest.py, main.py/app.py/__main__.py] + (b) files genoemd in feedback-tekst. Rest komt mee als `other_files_manifest`. Safety valve bij geen-matches.
2. **Functional tester herschreven**: plan-driven, httpx ipv curl-subprocess, regex path-param injectie (vangt `{id}`, `{todo_id}`, `{user_id}`, etc.), state tracking via POST→captured id, lenient status check (any 2xx tenzij plan expliciet `expected_status` zet), GET met `request_example` als query string.
3. **Test-isolation rule** (Developer-prompt sectie 0d): autouse `reset_state` fixture verplicht in tests/conftest.py *en* in elk test-bestand. Belt-and-suspenders — empirisch bleek dat conftest.py's autouse niet betrouwbaar firet in deze build/test-omgeving (root cause nog onbekend).
4. **Lessons-extractor manual run**: eerste echte multi-attempt success (library lending) gebruikt om lesson te extracten. Lesson empirisch correct ("duplicate fixture in test file") maar extractor's reasoning was workaround-tier (focus op diff, niet op mechanisme). Extractor-prompt heeft refinement nodig vóór pipeline-integratie.

### Validatie-cijfers

Pre-fix baseline: 22.2% first-attempt APPROVED (uit `docs/baseline-2026-05-06.md`).

Post-fix: **6/6 first-attempt APPROVED** op diverse task-types, gemiddeld ~2:00-2:30 per run:

| Service | Type | Resultaat |
|---|---|---|
| `todo_service` | Single-resource CRUD met path-params | 1 attempt (origineel bug-trigger) |
| `blog_service` | Nested resources (posts + comments) | 1 attempt |
| `movie_search_service` | CRUD + query-string filtering | 1 attempt |
| `user_registration_service` | CRUD met EmailStr/UUID validatie | 1 attempt |
| `unit_converter_service` | Stateless computatie | 1 attempt |
| `library_lending_system` | Multi-resource + state-machine + business rules | 1 attempt (na test-isolation update) |

### Empirische bevindingen

- **De truncation-bug was secundair**. De echte oorzaak van de oorspronkelijke todo-loop was de functional_tester die `{id}` placeholders niet substitueerde. Zelfde patroon als de GET-querystring vondst van 2026-05-08, andere variant. Bevestiging: bij rare loops eerst de tester checken voor de Developer-prompt aanraakt.
- **State-overwrite limiet in tester** (latent): bij blog_service slaagde de nested-resource flow toevallig omdat post_id_counter en comment_id_counter beide op 1 starten. Echte beperking surfaced via fragile pass.
- **Querystring code-path is dead in praktijk**: Planner zet `request_example: {}` voor GET, dus de querystring-tweak in tester wordt nooit aangeroepen. Pytest dekt filter-logica via TestClient. Niet schadelijk.
- **conftest.py autouse mystery**: in attempt_1 van library was de fixture syntactisch correct in tests/conftest.py, maar firet niet (bewezen door sequentiële IDs 1,2,3 over tests heen). Dezelfde fixture in test_routes.py firet wel. Onbekend waarom.
- **Recurring Judge-flags die de Developer niet uit zichzelf oplost**: POST 200 ipv 201 (REST conventie), in-memory zonder persistence-disclaimer, geen healthcheck in docker-compose. Patronen, niet incidenten.

## TODOs (in prioriteit volgorde)

### #1 — Diagnose conftest.py autouse mystery (MIDDEL)

Empirisch bewezen: conftest.py's autouse fixture firet niet betrouwbaar in deze build-omgeving. Workaround actief (belt-and-suspenders rule), maar root cause onbekend. Mogelijke kanten: pytest config in pyproject.toml, TestClient lifespan interactie, coverage-plugin interactie. Diagnose vereist lokaal reproduceren van attempt_1's code en pytest draaien met `--setup-show`.

### #2 — Schema-First Database Services (HOOG, project-scope)

User definieert schema als YAML/JSON; deterministisch script (geen LLM) genereert SQLAlchemy modellen + Alembic migrations + repository functies + standaard CRUD endpoints. LLM komt pas in beeld voor business rules bovenop schema-based fundament. Lost iteration 4's brittleness echt op. Geschat: een week geconcentreerd werk. Promovéert hierbij van "geparkeerd" naar kandidaat #1 voor volgende grote sessie.

### #3 — Tester per-resource state tracking (LAAG, latent)

`state["id"]` is één globale slot dat wordt overwriten bij elke POST. Werkt in 80%+ van CRUD-cases, faalt bij multi-resource flows met afwijkende id-conventies. Niet urgent — oppakken bij echte failure.

### #4 — Lessons-extractor refinement + pipeline-integratie (CONDITIONEEL)

Manual run validated dat extractor werkt en gestructureerde output produceert. Maar reasoning was diff-georiënteerd, niet mechanisme-georiënteerd. Voor pipeline-integratie: extractor-prompt versterken met "explain mechanism, not diff" + confidence threshold (≥ 0.7) + tweede-pass die check't "is dit een regel of een workaround?".

### #5 — Domain detection few-shot (LAAG, niet urgent)

Anekdotisch BMI-classificatie issue. Geen recente empirische trigger. Lage effort, lage urgentie.

### #6 — Iteration 5 voltooien (geparkeerd)

Phase 5A (HEALTHCHECK) gedaan. Phase 5B (non-root user + multi-stage Dockerfile + .github/workflows/ci.yml) staat geparkeerd. Opnieuw oppakken als concentrated effort, vergelijkbaar met Schema-First.

## Architectuur (compact)
┌──────────────────────────────────────────┐
│  Jouw machine                            │
│  python main.py "..."                     │
│    → run_factory_pipeline() (synchroon)   │
│  Pipeline:                                │
│   Planner → Developer → Builder           │
│        → Tester → Judge → git push        │
│  data/factory.db   ← lokale memory        │
│  Docker            ← build + test         │
│  (optioneel) Postgres via docker compose  │
└──────────────────────────────────────────┘

Flow per job: Planner → Developer (met retry-feedback indien nodig) → Builder → Tester (pytest + functional smoke) → Judge → git push. Eén proces, geen queue.

## Models per role

| Role | Model | Notes |
|---|---|---|
| planner | `~anthropic/claude-opus-latest` | |
| developer | `~google/gemini-pro-latest` | |
| developer_premium | `~anthropic/claude-opus-latest` | last attempt fallback |
| builder | `~deepseek/deepseek-v4-flash-latest` | |
| tester | `~deepseek/deepseek-v4-flash-latest` | |
| judge | `~anthropic/claude-sonnet-latest` | |
| consultant_scientific | `~google/gemini-pro-latest` | |

Globale `max_tokens: 32000`. Per-role timeouts: planner 180s, developer 600s, premium 900s, builder/tester 300s, judge 180s.

## Operational reference

### Daily workflow

```bash
cd ai-factory && source venv/bin/activate   # Windows: venv\Scripts\activate
python main.py "Make a service that..."
```

### Configuratie

- `.env` — API keys + optionele DATABASE_URL (zie `.env.example`)
- `src/llm/client.py` — MODEL_ROUTES + TIMEOUTS
- `src/workflow/pipeline.py` — `max_tester_attempts=6`, `max_judge_attempts=3`
- Service-template settings via env vars (zie `src/service_template/settings.py`)

### Bekende stabiele referentievoorbeelden

- `password_generator_service` (iteration 3) — full template validation
- `case_converter_service` (iteration 1 polish) — POST /convert/all
- `library_lending_system` (2026-05-09) — multi-resource CRUD met business rules

### Disk cleanup wanneer worker vol

```bash
docker system prune -a --volumes
```

## Resource usage

| VM | CPU | RAM | Disk |
|---|---|---|---|
| Orchestrator | 2 cores | 2 GB | ~5 GB |
| Worker | 2 cores | 4 GB | ~10 GB (Docker images) |
| Storage | 1 core | 1 GB | ~3 GB |

## Eerdere sessies (gearchiveerd)

### 2026-05-08 — Cumulative history + lessons-extractor v1 + functional tester GET-querystring fix

- Per-attempt code snapshots in `logs/snapshots/{job_id}/attempt_N/`
- Failing tests parsed per attempt (ANSI-tolerant)
- `failure_history` cross-attempt feedback
- Lessons-extractor v1 als standalone script (`scripts/extract_lessons.py`)
- functional_tester `urlencode(request_example)` voor GET requests

### 2026-05-07 — Rollback iter5 + Phase 5A HEALTHCHECK + per-attempt failure logging

- main op stable iter3-base, iter5 broken commits gearchiveerd als `main-archive-2026-05-06`
- Phase 5A HEALTHCHECK: alle services hebben Python-based HEALTHCHECK
- Pipeline failure logging gestructureerd (failure_context per attempt)
- Developer prompt incremental retry rules
- Incremental log persistence

## Iteration 4 (Database Integration) — bewust afgeschaald

In-memory storage is de default voor gegenereerde services. LLM-die-SQLAlchemy-schrijft was te brittle (Pydantic Settings monkeypatch issues, coverage gate fails op routes met DB-dependency). Resolution: Planner default `needs_database=false`, DB-services met de hand bouwen op de template-infrastructuur. `src/service_template/database.py` async SQLAlchemy is klaar en werkt. Schema-First (TODO #2) is de ware oplossing.
