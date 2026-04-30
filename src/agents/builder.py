import os
import json
from pathlib import Path

class BuilderAgent:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def run(self, plan: dict, dev_result: dict, attempt: int = 1) -> dict:
        project_name = plan["project_name"]
        project_path = self.output_dir / project_name

        # Archiveer vorige poging als die bestaat
        if attempt > 1 and project_path.exists():
            import shutil
            archive_dir = project_path / "_attempts" / f"attempt_{attempt - 1}"
            archive_dir.parent.mkdir(parents=True, exist_ok=True)
            # Kopieer alle huidige bestanden behalve de _attempts map zelf
            for item in project_path.iterdir():
                if item.name == "_attempts":
                    continue
                dest = archive_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        project_path.mkdir(parents=True, exist_ok=True)
        written = []

        # 1. Schrijf alle bestanden van de developer
        for f in dev_result["files"]:
            file_path = project_path / f["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f["content"])
            written.append(str(file_path))

        # 2. Voeg __init__.py toe in elke Python package map
        for sub_dir in project_path.rglob("*"):
            if sub_dir.is_dir() and sub_dir.name not in ["__pycache__", ".git"]:
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
        
        # Test dependencies altijd toevoegen
        guaranteed_test_deps = ["pytest", "httpx"]  # httpx voor FastAPI tests
        
        # Combineer alles, dedupe
        all_reqs = list(existing_reqs) + list(plan_reqs)
        for dep in guaranteed_test_deps:
            # Check of de dep al in een vorm aanwezig is (bv "pytest" of "pytest>=7")
            if not any(r.split("==")[0].split(">=")[0].split("<=")[0].strip() == dep for r in all_reqs):
                all_reqs.append(dep)
        
        # Schrijf gededupliceerde lijst
        seen = set()
        final_reqs = []
        for r in all_reqs:
            key = r.split("==")[0].split(">=")[0].split("<=")[0].strip()
            if key and key not in seen:
                seen.add(key)
                final_reqs.append(r)
        
        req_path.write_text("\n".join(final_reqs) + "\n")
        written.append(str(req_path))

        # 4. .env.example en lege .env (zodat docker-compose niet faalt)
        env_example = project_path / ".env.example"
        env_example.write_text("# Vul in en hernoem naar .env\n# Geen echte secrets committen!\n")
        written.append(str(env_example))

        env_real = project_path / ".env"
        if not env_real.exists():
            env_real.write_text("# Lokale env vars - niet committen\n")
            written.append(str(env_real))

        # 5. docker-compose.yml - alleen voor web apps
        # We detecteren web apps later, dus eerst Dockerfile-stap doen
        # Deze stap wordt verplaatst naar na de Dockerfile detectie
        compose_path = project_path / "docker-compose.yml"
        compose_pending = not compose_path.exists() 


        # 6. Dockerfile met PYTHONPATH zodat src.* imports werken
        dockerfile = project_path / "Dockerfile"
        if not dockerfile.exists():
            port = plan.get("docker_port", 8000)
            main_py = project_path / "src" / "main.py"
            entry_cmd = '["python", "-m", "src.main"]'  # default: -m flag laat src/ als package werken
            is_web_app = False

            if main_py.exists():
                content = main_py.read_text().lower()
                if "fastapi" in content:
                    entry_cmd = f'["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "{port}"]'
                    is_web_app = True
                elif "flask" in content:
                    entry_cmd = '["python", "-m", "src.main"]'
                    is_web_app = True

            expose_line = f"EXPOSE {port}\n" if is_web_app else ""
            dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

{expose_line}CMD {entry_cmd}
"""
            dockerfile.write_text(dockerfile_content)
            written.append(str(dockerfile))
            # docker-compose alleen voor web apps
            if compose_pending and is_web_app:
                port_compose = plan.get("docker_port", 8000)
                compose_content = f"""services:
  app:
    build: .
    ports:
      - "{port_compose}:{port_compose}"
    env_file:
      - .env
    restart: unless-stopped
"""
                compose_path.write_text(compose_content)
                written.append(str(compose_path))

        # 7. README.md - basis template als die niet bestaat
        readme_path = project_path / "README.md"
        if not readme_path.exists():
            port = plan.get("docker_port", 8000)
            main_py = project_path / "src" / "main.py"
            is_web = False
            if main_py.exists():
                content = main_py.read_text().lower()
                is_web = "fastapi" in content or "flask" in content

            if is_web:
                run_section = f"""## Lokaal draaien

```bash
docker-compose up --build
```

De service draait dan op http://localhost:{port}
"""
            else:
                run_section = f"""## Lokaal draaien

```bash
docker build -t {project_name} .
docker run --rm {project_name}
```

Voor een CLI tool met argumenten:
```bash
docker run --rm {project_name} python -m src.main --help
```
"""

            readme_content = f"""# {project_name}

{plan.get('description', 'AI-generated project')}

{run_section}
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
            "is_web_app": "EXPOSE" in dockerfile.read_text() if dockerfile.exists() else False
        }
