"""
Functional Tester — leest /openapi.json van de draaiende service en test elk endpoint
met fake bodies en path-param injectie. Spec-driven, niet plan-driven.
Voor CLI tools: simpele --help sanity check.
"""
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx


class FunctionalTester:
    def __init__(self):
        pass

    # -----------------------------
    # Docker helpers
    # -----------------------------
    def _cleanup(self, name: str) -> None:
        subprocess.run(["docker", "rm", "-f", name],
                       capture_output=True, timeout=10)

    def _logs(self, name: str) -> str:
        r = subprocess.run(["docker", "logs", name],
                           capture_output=True, text=True, timeout=10)
        return (r.stdout + "\n" + r.stderr)[-1500:]

    def _start_container(self, name: str, image: str, port: int) -> None:
        self._cleanup(name)
        subprocess.run([
            "docker", "run", "-d", "--rm",
            "--name", name,
            "-p", f"{port}:{port}",
            image
        ], check=True, capture_output=True, timeout=30)

    # -----------------------------
    # Readiness (wacht tot openapi.json reageert)
    # -----------------------------
    def _wait_ready(self, base_url: str, timeout: int = 25) -> bool:
        with httpx.Client(timeout=2.0) as client:
            start = time.time()
            while time.time() - start < timeout:
                try:
                    r = client.get(base_url + "/openapi.json")
                    if r.status_code == 200:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
        return False

    def _request(self, client, method, url, json_body=None, retries=3):
        last = None
        for _ in range(retries):
            try:
                return client.request(method, url, json=json_body)
            except Exception as e:
                last = e
                time.sleep(1)
        raise last

    # -----------------------------
    # Schema-driven body builder
    # Houdt rekening met simpele 'format' hints zodat strict-validators
    # (EmailStr, UUID, datetime, ...) niet falen op willekeurige strings.
    # -----------------------------
    def _fake_value(self, schema: dict) -> Any:
        if not isinstance(schema, dict):
            return None

        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        # union types: pak eerste niet-null optie
        for key in ("anyOf", "oneOf"):
            opts = schema.get(key)
            if isinstance(opts, list) and opts:
                for opt in opts:
                    if isinstance(opt, dict) and opt.get("type") != "null":
                        return self._fake_value(opt)
                return self._fake_value(opts[0])

        t = schema.get("type")
        fmt = schema.get("format", "")

        if t == "string":
            if fmt == "email":
                return "test@example.com"
            if fmt in ("uri", "url"):
                return "https://example.com"
            if fmt == "uuid":
                return "00000000-0000-0000-0000-000000000001"
            if fmt == "date":
                return "2024-01-01"
            if fmt == "date-time":
                return "2024-01-01T00:00:00Z"
            if fmt == "time":
                return "12:00:00"
            return "test"
        if t == "integer":
            return 1
        if t == "number":
            return 1.0
        if t == "boolean":
            return True
        if t == "array":
            return [self._fake_value(schema.get("items", {}))]
        if t == "object":
            props = schema.get("properties", {})
            return {k: self._fake_value(v) for k, v in props.items()}

        return None

    def _build_body(self, op: dict) -> Any:
        try:
            content = op.get("requestBody", {}).get("content", {})
            app_json = content.get("application/json")
            if not app_json:
                return None
            return self._fake_value(app_json.get("schema", {}))
        except Exception:
            return None

    # -----------------------------
    # Verwachte status uit OpenAPI (alleen 2xx codes meetellen)
    # -----------------------------
    def _expected_status(self, op: dict, method: str) -> int:
        responses = op.get("responses", {})
        success_codes = [int(c) for c in responses.keys()
                         if c.isdigit() and 200 <= int(c) < 300]
        if success_codes:
            return min(success_codes)
        if method == "POST":
            return 201
        return 200

    # -----------------------------
    # Path-param injectie: vervang elke placeholder met 'id' in de naam
    # ({id}, {user_id}, {postId}, {ITEM_ID}, ...)
    # -----------------------------
    def _inject_path_params(self, path: str, state: dict) -> str:
        if not state.get("id"):
            return path
        return re.sub(r"\{[^}]*[iI][dD][^}]*\}", str(state["id"]), path)

    # -----------------------------
    # Capture id uit response (recursief, accepteert *id keys)
    # -----------------------------
    def _extract_id(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(k, str) and k.lower().endswith("id"):
                    return v
            for v in obj.values():
                found = self._extract_id(v)
                if found is not None:
                    return found
        elif isinstance(obj, list) and obj:
            return self._extract_id(obj[0])
        return None

    # -----------------------------
    # Hoofdtest: lees openapi.json en test elk endpoint
    # -----------------------------
    def _run_service_tests(self, plan: dict, image_tag: str, port: int) -> dict:
        container = f"functest-{plan['project_name']}"
        base_url = f"http://127.0.0.1:{port}"

        try:
            self._start_container(container, image_tag, port)
        except subprocess.CalledProcessError as e:
            return {
                "passed": False,
                "scenarios_run": 0,
                "results": [{
                    "scenario": {"name": "container start"},
                    "evaluation": {"passed": False, "reasons": [str(e)]}
                }]
            }

        if not self._wait_ready(base_url):
            container_logs = self._logs(container)
            self._cleanup(container)
            return {
                "passed": False,
                "scenarios_run": 0,
                "results": [{
                    "scenario": {"name": "openapi ready"},
                    "evaluation": {"passed": False, "reasons": ["openapi not available"]},
                    "run": {"stdout": container_logs, "stderr": ""}
                }]
            }

        results = []
        all_passed = True
        state: dict = {}

        with httpx.Client(timeout=5.0) as client:
            try:
                spec = client.get(base_url + "/openapi.json").json()
                paths = spec.get("paths", {})

                for raw_path, methods in paths.items():
                    for method_name, op in methods.items():
                        # path-level parameters/summary overslaan
                        if method_name in ("parameters", "summary", "description") or not isinstance(op, dict):
                            continue

                        method = method_name.upper()
                        path = self._inject_path_params(raw_path, state)
                        url = base_url + path

                        body = self._build_body(op)
                        expected = self._expected_status(op, method)

                        try:
                            r = self._request(client, method, url, json_body=body)
                            status = r.status_code
                            text = r.text[:500]

                            # Lenient: elke 2xx is geslaagd, niet alleen exact match
                            passed = 200 <= status < 300
                            reasons = [] if passed else [
                                f"got {status} (expected {expected} or any 2xx)"
                            ]

                            if method == "POST" and passed:
                                try:
                                    new_id = self._extract_id(r.json())
                                    if new_id is not None:
                                        state["id"] = new_id
                                except Exception:
                                    pass

                            log_excerpt = "" if passed else self._logs(container)

                            if not passed:
                                all_passed = False
                                print(f"[functional]   FAIL: {method} {raw_path} → {status}")
                            else:
                                print(f"[functional]   OK: {method} {raw_path} → {status}")

                            results.append({
                                "scenario": {"name": f"{method} {raw_path}"},
                                "run": {
                                    "stdout": text,
                                    "stderr": log_excerpt,
                                    "exit_code": 0 if passed else 1
                                },
                                "evaluation": {
                                    "passed": passed,
                                    "reasons": reasons,
                                    "scenario_name": f"{method} {raw_path}"
                                }
                            })

                        except Exception as e:
                            all_passed = False
                            log_excerpt = self._logs(container)
                            results.append({
                                "scenario": {"name": f"{method} {raw_path}"},
                                "run": {
                                    "stdout": "",
                                    "stderr": f"{e}\n{log_excerpt}",
                                    "exit_code": -1
                                },
                                "evaluation": {
                                    "passed": False,
                                    "reasons": ["request failed"],
                                    "scenario_name": f"{method} {raw_path}"
                                }
                            })

            finally:
                self._cleanup(container)

        return {
            "passed": all_passed,
            "scenarios_run": len(results),
            "results": results
        }

    # -----------------------------
    # CLI fallback
    # -----------------------------
    def _run_cli_tests(self, project_path: Path, image_tag: str) -> dict:
        try:
            r = subprocess.run([
                "docker", "run", "--rm", image_tag,
                "python", "-m", "src.main", "--help"
            ], capture_output=True, text=True, timeout=20)
            passed = r.returncode == 0
            return {
                "passed": passed,
                "scenarios_run": 1,
                "results": [{
                    "scenario": {"name": "cli --help"},
                    "run": {
                        "stdout": r.stdout[:500],
                        "stderr": r.stderr[:500],
                        "exit_code": r.returncode
                    },
                    "evaluation": {
                        "passed": passed,
                        "reasons": [] if passed else ["non-zero exit"]
                    }
                }]
            }
        except Exception as e:
            return {
                "passed": False,
                "scenarios_run": 1,
                "results": [{
                    "scenario": {"name": "cli run"},
                    "run": {"stdout": "", "stderr": str(e), "exit_code": -1},
                    "evaluation": {"passed": False, "reasons": ["execution failed"]}
                }]
            }

    # -----------------------------
    # Entry point
    # -----------------------------
    def run(self, plan: dict, build_result: dict) -> dict:
        project_path = Path(build_result["project_path"])
        image_tag = f"ai-factory/{project_path.name}:test"

        is_service = build_result.get("is_web_app", False) or plan.get("is_service", False)

        if is_service:
            dockerfile = project_path / "Dockerfile"
            port = 8000
            if dockerfile.exists():
                content = dockerfile.read_text()
                m = re.search(r"EXPOSE\s+(\d+)", content)
                if m:
                    port = int(m.group(1))
            print(f"\n[functional] SERVICE test on port {port}")
            return self._run_service_tests(plan, image_tag, port)

        print("\n[functional] CLI test")
        return self._run_cli_tests(project_path, image_tag)
