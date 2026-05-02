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

        # Archiveer vorige poging als die bestaat
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

        # 1. Schrijf alle bestanden van de developer
        # MAAR: skip Dockerfile, docker-compose.yml, README.md - die maakt Builder zelf
        builder_owned = {"Dockerfile", "docker-compose.yml", "README.md"}
        for f in dev_result["files"]:
            if Path(f["path"]).name in builder_owned:
                continue  # negeer wat de Developer zou hebben gemaakt
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

        # 3. requirements.txt - met gegarandeerde test dependencies
        req_path = project_path / "requirements.txt"
        existing_reqs = []
        if req_path.exists():
            existing_reqs = [line.strip() for line in req_path.read_text().splitlines() if line.strip()]

        plan_reqs = plan.get("requirements", [])
        guaranteed_test_deps = ["pytest", "httpx"]

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

        # 4. .env.example en lege .env
        env_example = project_path / ".env.example"
        env_example.write_text("# Vul in en hernoem naar .env\n# Geen echte secrets committen!\n")
        written.append(str(env_example))

        env_real = project_path / ".env"
        if not env_real.exists():
            env_real.write_text("# Lokale env vars - niet committen\n")
            written.append(str(env_real))

        # 5. Dockerfile - altijd FastAPI service architectuur
        port = MemoryClient().allocate_port(project_name)
        is_web_app = True  # altijd service tenzij plan expliciet anders zegt
        if not plan.get("is_service", True):
            is_web_app = False

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
ENV SERVICE_PORT={port}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

{expose_line}CMD {entry_cmd}
"""
        dockerfile.write_text(dockerfile_content)
        written.append(str(dockerfile))

        # 6. docker-compose.yml - alleen voor web apps, ALTIJD overschrijven
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
            # CLI tool: verwijder verkeerde compose als die er staat
            compose_path.unlink()

        # 7. README.md - met curl voorbeelden uit het plan
        readme_path = project_path / "README.md"

        if is_web_app:
            run_section = f"""## Lokaal draaien

```bash
docker build -t {project_name} .
docker run --rm -p {port}:{port} {project_name}
```

De service draait dan op http://localhost:{port}
"""
            # Endpoints met curl voorbeelden
            endpoint_section = "\n## Endpoints en testcommando's\n"
            endpoints = plan.get("endpoints", [])
            if endpoints:
                for ep in endpoints:
                    endpoint_section += f"\n### {ep.get('method', 'GET')} {ep.get('path', '/')}\n"
                    if ep.get("description"):
                        endpoint_section += f"\n{ep['description']}\n"
                    curl = ep.get("curl_example", "")
                    if curl:
                        # Vervang PORT placeholder door echte poort
                        # Normaliseer alle hardcoded poorten in curl naar onze poort
                        import re as _re
                        curl = _re.sub(r":\d{4,5}(?=/|'|\")", f":{port}", curl)
                        curl = curl.replace("PORT", str(port))
            # Standaard health endpoint
            endpoint_section += f"\n### GET /health\n\n```bash\ncurl http://localhost:{port}/health\n```\n"
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
