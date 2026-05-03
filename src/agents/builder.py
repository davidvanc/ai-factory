import os
import json
from pathlib import Path
from src.llm.memory_client import MemoryClient


class BuilderAgent:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def run(self, plan: dict, dev_result: dict, attempt: int = 1) -> dict:
        project_name = plan["project_name"]
        project_path = self.output_dir / project_name

        # Archiveer vorige poging als die bestaat (best-effort, blokkeert nooit retry)
        if attempt > 1 and project_path.exists():
            import shutil
            try:
                archive_dir = project_path / "_attempts" / f"attempt_{attempt - 1}"
                archive_dir.parent.mkdir(parents=True, exist_ok=True)
                for item in project_path.iterdir():
                    if item.name == "_attempts":
                        continue
                    dest = archive_dir / item.name
                    try:
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        elif item.is_file():
                            shutil.copy2(item, dest)
                    except Exception as e:
                        print(f"[builder] kon {item.name} niet archiveren: {e}")
                        continue
            except Exception as e:
                print(f"[builder] archief-stap mislukt (niet kritiek): {e}")

        project_path.mkdir(parents=True, exist_ok=True)
        written = []

        # 0. Kopieer service template in elke service
        if plan.get("is_service", True):
            import shutil
            template_src = Path(__file__).parent.parent / "service_template"
            template_dst = project_path / "src" / "service_template"
            if template_src.exists():
                template_dst.parent.mkdir(parents=True, exist_ok=True)
                if template_dst.exists():
                    shutil.rmtree(template_dst)
                shutil.copytree(template_src, template_dst, ignore=shutil.ignore_patterns("__pycache__"))
                written.append(str(template_dst))

        # 1. Schrijf alle bestanden van de developer (skip Builder-owned)
        builder_owned = {"Dockerfile", "docker-compose.yml", "README.md"}
        for f in dev_result["files"]:
            if Path(f["path"]).name in builder_owned:
                continue
            file_path = project_path / f["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f["content"])
            written.append(str(file_path))

        # 2. Voeg __init__.py toe in elke Python package map
        for sub_dir in project_path.rglob("*"):
            if sub_dir.is_dir() and sub_dir.name not in ["__pycache__", ".git", "_attempts"]:
                py_files = list(sub_dir.glob("*.py"))
                init_file = sub_dir / "__init__.py"
                if py_files and not init_file.exists():
                    init_file.write_text("")
                    written.append(str(init_file))

        # 3. requirements.txt - met gegarandeerde dependencies
        req_path = project_path / "requirements.txt"
        existing_reqs = []
        if req_path.exists():
            existing_reqs = [line.strip() for line in req_path.read_text().splitlines() if line.strip()]

        plan_reqs = plan.get("requirements", [])
        guaranteed_test_deps = [
            "pytest", "pytest-asyncio>=0.21", "pytest-cov", "httpx",
            # Service template dependencies
            "fastapi", "uvicorn", "pydantic-settings>=2.0",
            "structlog", "prometheus-client>=0.20",
            # Iteration 2: security + resilience
            "slowapi", "redis",
            # Iteration 3: testing + docs
            "email-validator"
        ]
        all_reqs = list(existing_reqs) + list(plan_reqs)
        for dep in guaranteed_test_deps:
            if not any(r.split("==")[0].split(">=")[0].split("<=")[0].strip() == dep for r in all_reqs):
                all_reqs.append(dep)

        seen = set()
        final_reqs = []
        for r in all_reqs:
            key = r.split("==")[0].split(">=")[0].split("<=")[0].strip()
            if key and key not in seen:
                seen.add(key)
                final_reqs.append(r)

        req_path.write_text("\n".join(final_reqs) + "\n")
        written.append(str(req_path))

        # 3b. pyproject.toml met pytest + coverage configuratie
        if plan.get("is_service", True):
            template_pyproject = Path(__file__).parent.parent / "service_template" / "pyproject_template.toml"
            if template_pyproject.exists():
                target_pyproject = project_path / "pyproject.toml"
                target_pyproject.write_text(template_pyproject.read_text())
                written.append(str(target_pyproject))

        # 3c. tests/conftest.py met shared fixtures
        if plan.get("is_service", True):
            tests_dir = project_path / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            conftest_path = tests_dir / "conftest.py"
            conftest_path.write_text('''"""Shared test fixtures (auto-generated)."""
from src.service_template.test_fixtures import client, anyio_backend, auth_headers, reset_settings  # noqa: F401
''')
            written.append(str(conftest_path))

        # 3d. tests/test_template_contract.py met standaard contract tests
        if plan.get("is_service", True):
            template_contract = Path(__file__).parent.parent / "service_template" / "contract_tests.py"
            if template_contract.exists():
                target_contract = project_path / "tests" / "test_template_contract.py"
                # Kopieer maar zonder de docstring header van het template-bestand
                content = template_contract.read_text()
                target_contract.write_text(content)
                written.append(str(target_contract))

        # 3e. ADR.md met architectuur-beslissingen
        if plan.get("is_service", True):
            from src.service_template.adr_template import generate_adr
            adr_path = project_path / "ADR.md"
            adr_path.write_text(generate_adr(project_name, plan.get("description", "")))
            written.append(str(adr_path))

        # 4. .env.example en lege .env
        env_example = project_path / ".env.example"
        env_example.write_text("# Vul in en hernoem naar .env\n# Geen echte secrets committen!\n")
        written.append(str(env_example))

        env_real = project_path / ".env"
        if not env_real.exists():
            env_real.write_text("# Lokale env vars - niet committen\n")
            written.append(str(env_real))

        # 5. Dockerfile
        port = MemoryClient().allocate_port(project_name)
        is_web_app = plan.get("is_service", True)

        if is_web_app:
            entry_cmd = f'["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "{port}"]'
            expose_line = f"EXPOSE {port}\n"
        else:
            entry_cmd = '["python", "-m", "src.main"]'
            expose_line = ""

        dockerfile = project_path / "Dockerfile"
        dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME={project_name}
ENV SERVICE_VERSION=0.1.0
ENV PORT={port}
ENV ENVIRONMENT=dev
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO
ENV AUTH_ENABLED=false
ENV AUTH_TOKENS=
ENV ALLOWED_ORIGINS=*
ENV RATE_LIMIT_ENABLED=false
ENV RATE_LIMIT_PER_MINUTE=60
ENV RATE_LIMIT_REDIS_URL=redis://localhost:6379/1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

{expose_line}CMD {entry_cmd}
"""
        dockerfile.write_text(dockerfile_content)
        written.append(str(dockerfile))

        # 6. docker-compose.yml
        compose_path = project_path / "docker-compose.yml"
        if is_web_app:
            compose_content = f"""services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env
    restart: unless-stopped
"""
            compose_path.write_text(compose_content)
            written.append(str(compose_path))
        elif compose_path.exists():
            compose_path.unlink()

        # 7. README.md
        readme_path = project_path / "README.md"

        if is_web_app:
            run_section = f"""## Lokaal draaien

```bash
docker build -t {project_name} .
docker run --rm -p {port}:{port} {project_name}
```

De service draait dan op http://localhost:{port}
"""
            endpoint_section = "\n## Endpoints en testcommando's\n"
            endpoints = plan.get("endpoints", [])
            template_paths = {"/health", "/ready", "/metrics"}
            endpoints_business = [ep for ep in endpoints if ep.get("path") not in template_paths]

            if endpoints_business:
                for ep in endpoints_business:
                    endpoint_section += f"\n### {ep.get('method', 'GET')} {ep.get('path', '/')}\n"
                    if ep.get("description"):
                        endpoint_section += f"\n{ep['description']}\n"
                    curl = ep.get("curl_example", "")
                    if not curl:
                        method = ep.get("method", "GET").upper()
                        path = ep.get("path", "/")
                        body = ep.get("request_example")
                        if method in ("POST", "PUT", "PATCH") and body:
                            body_str = json.dumps(body, ensure_ascii=False).replace("'", "\\'")
                            curl = f"curl -X {method} http://localhost:PORT{path} -H 'Content-Type: application/json' -d '{body_str}'"
                        else:
                            curl = f"curl -X {method} 'http://localhost:PORT{path}'"

                    if curl:
                        import re as _re
                        curl = _re.sub(r":\d{4,5}(?=/|'|\")", f":{port}", curl)
                        curl = curl.replace("PORT", str(port))
                        endpoint_section += f"\n```bash\n{curl}\n```\n"
                    if ep.get("response_example"):
                        endpoint_section += f"\n**Response:**\n```json\n{json.dumps(ep['response_example'], indent=2, ensure_ascii=False)}\n```\n"

            endpoint_section += f"\n## Standaard endpoints (van service template)\n\n"
            endpoint_section += f"```bash\n"
            endpoint_section += f"curl http://localhost:{port}/health    # liveness probe\n"
            endpoint_section += f"curl http://localhost:{port}/ready     # readiness probe\n"
            endpoint_section += f"curl http://localhost:{port}/metrics   # Prometheus metrics\n"
            endpoint_section += f"open http://localhost:{port}/docs      # OpenAPI documentation\n"
            endpoint_section += f"```\n"
        else:
            run_section = f"""## Lokaal draaien

```bash
docker build -t {project_name} .
docker run --rm {project_name}
```
"""
            endpoint_section = ""

        readme_content = f"""# {project_name}

{plan.get('description', 'AI-generated service')}

{run_section}
{endpoint_section}

## Tests draaien

```bash
docker run --rm {project_name} python -m pytest tests/ -v
```

## Project structuur

- `src/` - source code
- `tests/` - tests
- `Dockerfile` - container definitie
- `requirements.txt` - Python dependencies
- `.env.example` - voorbeeld environment variabelen

## Configuratie

Kopieer `.env.example` naar `.env` en pas aan indien nodig:

```bash
cp .env.example .env
```

---
*Auto-generated by AI Software Factory*
"""
        readme_path.write_text(readme_content)
        written.append(str(readme_path))

        # 8. .gitignore
        gitignore = project_path / ".gitignore"
        gitignore.write_text(".env\n__pycache__/\n*.pyc\nvenv/\n.pytest_cache/\n")
        written.append(str(gitignore))

        return {
            "project_path": str(project_path),
            "files_written": written,
            "file_count": len(written),
            "is_web_app": is_web_app
        }
