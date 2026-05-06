AI Software Factory
> Autonomous multi-agent AI software factory. Give it a description, get a production-grade microservice on GitHub.
For full context see `HANDOVER.md`.
For technical state see `PROJECT\_STATE.md`.
---
What It Does
You write:
> "Make a service that converts hex colors to RGB and HSL"
The system:
Plans the architecture
Writes the code
Builds a Docker image
Tests it (unit + integration + functional HTTP smoke tests)
Has an AI judge review it
Pushes to GitHub if approved
Records what worked and what didn't
In about 2-4 minutes per service.
---
Quick Start
Prerequisites
You need three Linux VMs networked together. See `HANDOVER.md` section 2 for the exact infrastructure.
Daily workflow
Terminal 1: Worker VM
```bash
cd \~/ai-factory-worker
source venv/bin/activate
rq worker --url redis://192.168.129.20:6379 factory
```
Leave this running. You'll see live agent output here.
Terminal 2: Orchestrator VM
```bash
cd \~/ai-factory
source venv/bin/activate
python submit.py "Make a service that does X"
```
The submit returns immediately with a job ID. Watch Terminal 1 for progress.
Test a generated service
```bash
# On Worker VM
cd \~/ai-factory-worker
docker images | grep ai-factory  # Find the image
docker run -d --rm --name svc -p PORT:PORT ai-factory/SERVICE\_NAME:test
sleep 4

curl http://localhost:PORT/health
# {"status":"ok"}

# Check the README in the generated service for the right curl command
cat output/SERVICE\_NAME/README.md

# When done
docker stop svc
```
---
Architecture (One Diagram)
```
┌──────────────────────┐
│  Orchestrator VM     │  ← you submit jobs here
│  192.168.128.197     │
└──────────┬───────────┘
           │ enqueue
           ▼
┌──────────────────────┐
│  Storage VM          │  ← Redis + Memory + Postgres
│  192.168.129.20      │
│  - Redis :6379       │
│  - Memory :8765      │
│  - Postgres :5432    │
└──────────┬───────────┘
           │ dequeue
           ▼
┌──────────────────────┐
│  Worker VM           │  ← actually runs the pipeline
│  192.168.129.82      │
│  Pipeline:           │
│   Planner            │
│   Developer          │
│   Builder            │
│   Tester             │
│   Judge              │
│   → git push         │
└──────────────────────┘
```
---
Daily Operations Cheatsheet
Submit a job
```bash
# Orchestrator VM
cd \~/ai-factory \&\& source venv/bin/activate
python submit.py "Make a service that does X"
```
Check queue status
```bash
# Any VM with venv active
rq info --url redis://192.168.129.20:6379
```
Check memory stats
```bash
curl -s http://192.168.129.20:8765/stats | python3 -m json.tool
```
Check allocated ports
```bash
curl -s http://192.168.129.20:8765/ports | python3 -m json.tool
```
Check recent projects
```bash
curl -s http://192.168.129.20:8765/projects?limit=5 | python3 -m json.tool
```
Inspect last run log
```bash
# Worker VM
ls -t \~/ai-factory-worker/logs/job\_\*.json | head -1 | xargs cat | python3 -m json.tool
```
Force cleanup of zombie containers
```bash
# Worker VM
docker stop $(docker ps -aq) 2>/dev/null
docker rm -f $(docker ps -aq) 2>/dev/null
```
Reset a specific service for re-generation
```bash
# Worker VM
rm -rf \~/ai-factory-worker/output/SERVICE\_NAME
docker rmi ai-factory/SERVICE\_NAME:test 2>/dev/null
```
Sync code changes between VMs
```bash
# Always via Git, never direct file copy

# On Orchestrator after editing code
cd \~/ai-factory
git add -A
git commit -m "Description"
git pull --rebase
git push

# On Worker
cd \~/ai-factory-worker
git pull
```
---
Common Tasks
Add a new dependency to all generated services
Edit `\~/ai-factory/src/agents/builder.py`, find `guaranteed\_test\_deps`, add the package:
```python
guaranteed\_test\_deps = \[
    "pytest", "pytest-asyncio>=0.21", "pytest-cov", "httpx",
    "fastapi", "uvicorn", "pydantic-settings>=2.0",
    "structlog", "prometheus-client>=0.20",
    "slowapi", "redis",
    "email-validator",
    "your-new-dep",  # ← add here
]
```
Commit, push, pull on Worker, restart RQ worker. Next generated service will have it.
Change a model used by an agent
Edit `\~/ai-factory/src/llm/client.py`, find `MODEL\_ROUTES`:
```python
MODEL\_ROUTES = {
    "developer": "\~google/gemini-pro-latest",  # ← change here
    ...
}
```
Same commit/push/pull cycle as above.
Disable a feature in a deployed service
All settings are env vars. To disable rate limiting in a running container:
```bash
docker run -e RATE\_LIMIT\_ENABLED=false ...
```
For docker-compose:
```yaml
environment:
  RATE\_LIMIT\_ENABLED: "false"
```
See `\~/ai-factory/src/service\_template/settings.py` for the complete list.
Trigger premium model on a hard task
The pipeline auto-escalates to `developer\_premium` (Claude Opus 4.7) on the last attempt. To force it earlier, you'd need to patch `pipeline.py`.
Change retry counts
In `\~/ai-factory/src/workflow/pipeline.py`:
```python
def run\_factory\_pipeline(task: str, max\_tester\_attempts: int = 6, max\_judge\_attempts: int = 3) -> dict:
```
Or pass them via `submit.py` (would need extra args added).
Test the system end-to-end with a known-good task
```bash
# Submit
python submit.py "Make a service with POST /reverse that reverses a string"

# Should complete in \~2-3 minutes with first-poging APPROVED
```
If THIS fails, something fundamental is broken. See `PROJECT\_STATE.md` for the latest known-good state.
---
Troubleshooting
Pipeline says "Successfully completed" in 7 seconds
That's a crash, not a success. The error is in the log file.
```bash
# Worker
ls -t \~/ai-factory-worker/logs/job\_\*.json | head -1 | xargs cat | python3 -m json.tool | tail -10
```
Look for `"status": "error"` and the message.
Common 7-second crashes:
`Invalid format specifier` → f-string bug, search for dict literals in `\*.py`
`KeyError` → plan structure changed but code references old field
`Module not found` → dependency missing on the Worker venv
Pipeline hangs for 15 minutes
LLM stream is stuck. Usually with DeepSeek V4 Pro (degeneration loops). We have a 90s idle timeout that should catch it. If not:
Ctrl+C on the Worker
Check the model in use — switch to Gemini Pro Latest if it's DeepSeek
Check if `max\_tokens: 32000` is set in `client.py`
Tests pass but functional smoke test fails
Service starts but endpoints don't respond. Common causes:
Port mismatch: service runs on port X but Tester checks port Y. Verify with:
```bash
  cat output/SERVICE\_NAME/Dockerfile | grep PORT
  ```
Service crashed at startup. Run manually:
```bash
  docker run -p PORT:PORT ai-factory/SERVICE\_NAME:test
  ```
DB connection: if needs_database=true and Postgres isn't reachable, service may crash
"git push rejected"
Worker pushed something while Orchestrator was working:
```bash
git pull --rebase
git push
```
Postgres connection fails
Check from Orchestrator:
```bash
psql -h 192.168.129.20 -U factory\_admin -d factory\_main -c "SELECT 1;"
```
If it asks for a password and rejects yours: the `@` in your password needs URL-encoding (`%40`) when used in `DATABASE\_URL`. The plain password without encoding works for `psql -U` because it's a separate field.
Memory service unreachable
```bash
curl http://192.168.129.20:8765/stats
```
If this fails:
```bash
# On Storage VM
sudo systemctl status memory-service
sudo systemctl restart memory-service
sudo journalctl -u memory-service --since "5 minutes ago"
```
Out of disk space on Worker
```bash
docker system prune -a --volumes  # nukes all unused Docker resources
```
"Address already in use" when starting service
A previous container didn't stop. Kill all factory containers:
```bash
docker ps -a | grep ai-factory | awk '{print $1}' | xargs docker rm -f
```
---
What Just Happened? Reading the Output
When a job runs on the Worker, you see something like:
```
\[planner] domein detectie: \['general'] (high, keywords)
\[planner via anthropic/claude-opus-4-7] streaming...
{...JSON plan...}
\[developer via \~google/gemini-pro-latest] streaming...
{...JSON files...}
\[tester] 1/3 docker build ai-factory/SERVICE\_NAME:test...
\[tester] docker build OK
\[tester] 2/3 pytest...
\[tester] pytest OK
\[tester] 3/3 runtime startup test...
\[tester] runtime OK (container draait stabiel)
\[tester] 4/4 functional smoke test...
\[functional] testing as SERVICE on port 8014
\[functional]   OK: GET /health → HTTP 200
\[functional]   OK: POST /endpoint1 → HTTP 200
\[git] SERVICE\_NAME ECHT gepusht (poging 1)
Successfully completed ... in 0:02:32.123456s
```
Reading this:
Every fase prints its name
`OK` / `FAIL` markers tell you progress
`streaming...` is the LLM thinking (you'll see live tokens flowing)
Final timing tells you total pipeline duration
If you see streaming for too long without progress, hit Ctrl+C and check the log.
---
What's Configured Where
Service template settings (in generated services)
Available env vars (set in docker run or .env):
Var	Default	What
`SERVICE\_NAME`	unnamed-service	Service identity in logs
`SERVICE\_VERSION`	0.1.0	Version
`ENVIRONMENT`	dev	dev/staging/prod
`PORT`	8000	HTTP listen port
`LOG\_LEVEL`	INFO	DEBUG/INFO/WARNING/ERROR
`LOG\_FORMAT`	json	json/console
`AUTH\_ENABLED`	false	Require Bearer token
`AUTH\_TOKENS`	(empty)	Comma-separated valid tokens
`ALLOWED\_ORIGINS`	*	CORS origins
`RATE\_LIMIT\_ENABLED`	false	Enable per-IP rate limit
`RATE\_LIMIT\_PER\_MINUTE`	60	Limit value
`RATE\_LIMIT\_REDIS\_URL`	redis://localhost:6379/1	Backend
`MAX\_REQUEST\_BODY\_BYTES`	1048576	1MB request limit
`REQUEST\_TIMEOUT\_SECONDS`	30	Per-request timeout
`DATABASE\_ENABLED`	false	Enable Postgres
`DATABASE\_URL`	(set)	Connection string
`DATABASE\_POOL\_SIZE`	5	Connection pool
Factory configuration
In `\~/ai-factory/.env`:
```
OPENROUTER\_API\_KEY=sk-or-...
FIRECRAWL\_API\_KEY=fc-...
POSTGRES\_PASSWORD=<your password>
DATABASE\_URL=postgresql://factory\_admin:<URL-encoded password>@192.168.129.20:5432/factory\_main
DATABASE\_ENABLED=true
ORCHESTRATOR\_IP=192.168.128.197
WORKER\_IP=192.168.129.82
STORAGE\_IP=192.168.129.20
REDIS\_URL=redis://192.168.129.20:6379
LOG\_LEVEL=INFO
```
---
Operational Limits
These are limits we know about — exceeding them might break things.
Limit	Value	Why
Pipeline timeout	30 minutes per job	RQ default
LLM stream idle	90 seconds	Catches stuck streams
LLM max output	32,000 tokens	Prevents degeneration
Pipeline retries (test)	6 attempts	Then bail out
Pipeline retries (judge)	3 attempts	Then mark failed
Service ports	8001-9000	Allocated incrementally
Service body size	1 MB	Configurable per service
Service request timeout	30s	Configurable per service
Memory SQLite	(no enforced limit)	Periodic cleanup advisable
Firecrawl free tier	500 credits	~500 page fetches/month
Postgres connections	100 (default)	Adjust per workload
---
What This System Is NOT
Setting expectations clearly:
❌ NOT a replacement for human code review for production-critical paths
❌ NOT for security-sensitive applications (banking, medical) without audit
❌ NOT a GUI — everything is CLI/HTTP
❌ NOT a real-time system (LLM calls take seconds)
❌ NOT certifiable enterprise-grade (no SOC 2, no compliance officer, no liability)
❌ NOT for stateful applications with complex DB schemas (write by hand)
❌ NOT cheaper than a developer for one-off scripts (LLM costs add up)
This system IS very good at:
✅ Generating consistent boilerplate-heavy services in minutes
✅ Producing services with consistent quality (logging, metrics, security headers)
✅ Demonstrating microservice patterns to learners
✅ Quickly prototyping ideas before deciding if they're worth manual development
---
Future Roadmap (David's notes)
Things David mentioned wanting to explore:
Trading bot (paused — too complex for autonomous generation)
Bio age calculator (good Scientific Consultant test case)
Star Trek fanpage (Scraper Consultant test — works after public-sites prompt fix)
Real production deployment with CI/CD pipeline
Service-to-service communication patterns
Stateful services with hand-written database code
---
Need Help?
Read in this order:
This README (operational)
`PROJECT\_STATE.md` (current technical state)
`HANDOVER.md` (full context and history)
If you're a new Claude session: please read all three before suggesting changes. The owner has invested significant time and shouldn't have to re-teach context.
---
License
Internal project, not for distribution. Code generated by this system is owned by David Vanc.
