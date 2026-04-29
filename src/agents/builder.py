import os
import json
from pathlib import Path

class BuilderAgent:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def run(self, plan: dict, dev_result: dict) -> dict:
        project_name = plan["project_name"]
        project_path = self.output_dir / project_name

        # Maak project map aan (overschrijf indien bestaat)
        project_path.mkdir(parents=True, exist_ok=True)

        written = []

        # Schrijf alle bestanden van de developer
        for f in dev_result["files"]:
            file_path = project_path / f["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f["content"])
            written.append(str(file_path))

        # Genereer requirements.txt als die niet bestaat
        req_path = project_path / "requirements.txt"
        if not req_path.exists():
            req_path.write_text("\n".join(plan["requirements"]) + "\n")
            written.append(str(req_path))

        # Genereer .env.example
        env_example = project_path / ".env.example"
        env_example.write_text("# Vul deze waarden in en hernoem naar .env\n# Geen echte secrets committen!\n")
        written.append(str(env_example))

        # Genereer docker-compose.yml als die niet bestaat
        compose_path = project_path / "docker-compose.yml"
        if not compose_path.exists():
            port = plan.get("docker_port", 8000)
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
        # Genereer Dockerfile als die niet bestaat
        dockerfile = project_path / "Dockerfile"
        if not dockerfile.exists():
            port = plan.get("docker_port", 8000)
            main_py = project_path / "src" / "main.py"
            cmd = '["python", "src/main.py"]'
            if main_py.exists():
                content = main_py.read_text().lower()
                if "fastapi" in content:
                    cmd = f'["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "{port}"]'

            dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD {cmd}
"""
            dockerfile.write_text(dockerfile_content)
            written.append(str(dockerfile))
        # Genereer .gitignore
        gitignore = project_path / ".gitignore"
        gitignore.write_text(".env\n__pycache__/\n*.pyc\nvenv/\n.pytest_cache/\n")
        written.append(str(gitignore))

        return {
            "project_path": str(project_path),
            "files_written": written,
            "file_count": len(written)
        }
