"""
Functional Tester — bedenkt en draait echte smoke tests op het gegenereerde project.
Voor microservices: start container, doe HTTP calls naar endpoints uit het plan.
Voor CLI tools: roep aan met argumenten en check stdout.
"""
import json
import subprocess
import time
import socket
from pathlib import Path
from src.llm.client import LLMClient
from src.llm.json_utils import extract_json
from urllib.parse import urlencode


def _wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 30) -> bool:
    """Wacht tot er een echt HTTP response komt. TCP connect alleen is niet genoeg."""
    import urllib.request
    import urllib.error
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"http://{host}:{port}/", method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                return True
        except urllib.error.HTTPError:
            # 404 of 405 is OK - de service luistert wel
            return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError, TimeoutError):
            time.sleep(0.5)
    return False

class FunctionalTester:
    def __init__(self):
        self.llm = LLMClient()

    def _run_service_tests(self, plan: dict, image_tag: str, port: int) -> dict:
        """Test FastAPI service door echte HTTP calls te doen."""
        container_name = f"functest-{plan['project_name']}"

        # Eerste cleanup
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=10)

        # Start container in background, mapped naar dezelfde poort
        try:
            subprocess.run([
                "docker", "run", "-d", "--rm",
                "--name", container_name,
                "-p", f"{port}:{port}",
                image_tag
            ], check=True, capture_output=True, timeout=30)
        except subprocess.CalledProcessError as e:
            return {
                "passed": False,
                "scenarios_run": 0,
                "results": [{
                    "scenario": {"name": "container start"},
                    "evaluation": {"passed": False, "reasons": [f"start failed: {e.stderr.decode()[:200]}"]}
                }]
            }

        # Wacht tot service luistert
        if not _wait_for_port(port, timeout=20):
            logs = subprocess.run(["docker", "logs", container_name],
                                  capture_output=True, text=True, timeout=10)
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=10)
            return {
                "passed": False,
                "scenarios_run": 0,
                "results": [{
                    "scenario": {"name": "service ready"},
                    "evaluation": {"passed": False, "reasons": [f"port {port} not listening after 20s"]},
                    "run": {"stderr": logs.stderr[-500:], "stdout": logs.stdout[-500:]}
                }]
            }

        # Test elk endpoint uit het plan + altijd /health
        endpoints = list(plan.get("endpoints", []))
        # Voeg /health toe als die niet in de lijst staat
        if not any(ep.get("path") == "/health" for ep in endpoints):
            endpoints.append({
                "method": "GET",
                "path": "/health",
                "description": "health check"
            })

        results = []
        all_passed = True

        try:
            for ep in endpoints:
                method = ep.get("method", "GET").upper()
                path = ep.get("path", "/")
                request_body = ep.get("request_example")

                url = f"http://localhost:{port}{path}"
                if method == "GET" and request_body and isinstance(request_body, dict):
                    try:
                        qs_params = {k: v for k, v in request_body.items() if v is not None}
                        if qs_params:
                            url = f"{url}?{urlencode(qs_params)}"
                    except (TypeError, ValueError):
                        pass  # ongeldige query values, fallback op base url

                cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "-X", method, url]
                if request_body and method in ("POST", "PUT", "PATCH"):
                    cmd.extend(["-H", "Content-Type: application/json",
                                "-d", json.dumps(request_body)])

                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    status_code = r.stdout.strip()
                    # Ook de body ophalen voor inspectie
                    body_cmd = ["curl", "-s", "-X", method, url]
                    if request_body and method in ("POST", "PUT", "PATCH"):
                        body_cmd.extend(["-H", "Content-Type: application/json",
                                         "-d", json.dumps(request_body)])
                    body_r = subprocess.run(body_cmd, capture_output=True, text=True, timeout=10)
                    body = body_r.stdout[:500]

                    accept = (200 <= int(status_code) < 300) if status_code.isdigit() else False
                    reasons = [] if accept else [f"got HTTP {status_code} (expected 2xx)"]

                    results.append({
                        "scenario": {"name": f"{method} {path}", "args": []},
                        "run": {"stdout": body, "stderr": "", "exit_code": 0 if accept else 1},
                        "evaluation": {"passed": accept, "reasons": reasons, "scenario_name": f"{method} {path}"}
                    })
                    if not accept:
                        all_passed = False
                        print(f"[functional]   FAIL: {method} {path} → HTTP {status_code}")
                    else:
                        print(f"[functional]   OK: {method} {path} → HTTP {status_code}")
                except subprocess.TimeoutExpired:
                    all_passed = False
                    results.append({
                        "scenario": {"name": f"{method} {path}", "args": []},
                        "run": {"stdout": "", "stderr": "TIMEOUT", "exit_code": -1},
                        "evaluation": {"passed": False, "reasons": ["timeout"], "scenario_name": f"{method} {path}"}
                    })

        finally:
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=15)

        return {
            "passed": all_passed,
            "scenarios_run": len(results),
            "results": results
        }

    def _run_cli_tests(self, plan: dict, project_path: Path, image_tag: str) -> dict:
        """Voor CLI tools: bedenk scenarios en draai ze als argumenten."""
        main_py = project_path / "src" / "main.py"
        main_content = main_py.read_text() if main_py.exists() else ""

        prompt = f"""Een Python CLI is net gebouwd. Genereer 2-3 SMOKE TESTS die het echt aanroepen.

Project: {plan['project_name']}
Beschrijving: {plan.get('description', '')}

src/main.py:
```python
{main_content[:3000]}
```

Antwoord ALLEEN met JSON:
{{
  "scenarios": [
    {{
      "name": "korte beschrijving",
      "args": ["arg1", "arg2"],
      "expect_in_stdout": ["string"],
      "expect_no_error": true
    }}
  ]
}}"""

        response = self.llm.generate(prompt, role="judge", temperature=0.3, stream=False)
        result = extract_json(response, expect="object")
        scenarios = result.get("scenarios", []) if result else []

        if not scenarios:
            return {"passed": True, "scenarios_run": 0, "results": []}

        results = []
        all_passed = True

        for scenario in scenarios:
            cmd = ["docker", "run", "--rm", image_tag, "python", "-m", "src.main"]
            cmd.extend(scenario.get("args", []))
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                run_result = {
                    "exit_code": r.returncode,
                    "stdout": r.stdout,
                    "stderr": r.stderr
                }
            except subprocess.TimeoutExpired:
                run_result = {"exit_code": -1, "stdout": "", "stderr": "TIMEOUT"}

            passed = True
            reasons = []
            if scenario.get("expect_no_error", True) and run_result["exit_code"] != 0:
                passed = False
                reasons.append(f"exit code {run_result['exit_code']}")

            stderr_lower = run_result["stderr"].lower()
            if any(kw in stderr_lower for kw in ["traceback", "modulenotfounderror", "syntaxerror", "importerror"]):
                passed = False
                reasons.append("crash detected")

            for expected in scenario.get("expect_in_stdout", []):
                if expected.lower() not in run_result["stdout"].lower():
                    passed = False
                    reasons.append(f"missing: '{expected}'")

            if not passed:
                all_passed = False
                print(f"[functional]   FAIL: {scenario.get('name')}: {reasons}")
            else:
                print(f"[functional]   OK: {scenario.get('name')}")

            results.append({
                "scenario": scenario,
                "run": run_result,
                "evaluation": {"passed": passed, "reasons": reasons, "scenario_name": scenario.get("name", "")}
            })

        return {"passed": all_passed, "scenarios_run": len(results), "results": results}

    def run(self, plan: dict, build_result: dict) -> dict:
        project_path = Path(build_result["project_path"])
        project_name = project_path.name
        image_tag = f"ai-factory/{project_name}:test"
        is_service = build_result.get("is_web_app", False) or plan.get("is_service", False)

        if is_service:
            # Lees Dockerfile om de poort te vinden
            dockerfile = project_path / "Dockerfile"
            port = 8000
            if dockerfile.exists():
                content = dockerfile.read_text()
                import re
                m = re.search(r"EXPOSE\s+(\d+)", content)
                if m:
                    port = int(m.group(1))

            print(f"\n[functional] testing as SERVICE on port {port}")
            return self._run_service_tests(plan, image_tag, port)
        else:
            print(f"\n[functional] testing as CLI tool")
            return self._run_cli_tests(plan, project_path, image_tag)
