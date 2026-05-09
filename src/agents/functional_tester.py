import json
import subprocess
import time
import re
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlencode

import httpx


class FunctionalTester:
    def __init__(self):
        pass

    # ---------------------------
    # Docker helpers
    # ---------------------------
    def _cleanup(self, name: str):
        subprocess.run(["docker", "rm", "-f", name],
                       capture_output=True, timeout=10)

    def _logs(self, name: str) -> str:
        r = subprocess.run(["docker", "logs", name],
                           capture_output=True, text=True, timeout=10)
        return (r.stdout + "\n" + r.stderr)[-1500:]

    def _start_container(self, name: str, image: str, port: int):
        self._cleanup(name)
        subprocess.run([
            "docker", "run", "-d", "--rm",
            "--name", name,
            "-p", f"{port}:{port}",
            image
        ], check=True, capture_output=True, timeout=30)

    # ---------------------------
    # Readiness
    # ---------------------------
    def _wait_ready(self, base_url: str, timeout=25) -> bool:
        paths = ["/health", "/", "/docs", "/openapi.json"]

        start = time.time()
        with httpx.Client(timeout=2.0) as client:
            while time.time() - start < timeout:
                for p in paths:
                    try:
                        r = client.get(base_url + p)
                        if r.status_code < 500:
                            return True
                    except Exception:
                        pass
                time.sleep(0.5)
        return False

    # ---------------------------
    # HTTP helpers
    # ---------------------------
    def _request(self, client, method, url, json_body=None, retries=3):
        last = None
        for _ in range(retries):
            try:
                return client.request(method, url, json=json_body)
            except Exception as e:
                last = e
                time.sleep(1)
        raise last

    def _infer_expected_status(self, ep: Dict[str, Any]) -> int:
        if "expected_status" in ep:
            return ep["expected_status"]

        desc = (ep.get("description") or "").lower()

        if "404" in desc:
            return 404
        if "422" in desc or "validation" in desc:
            return 422
        if ep.get("method", "").upper() == "POST":
            return 201

        return 200

    # ---------------------------
    # Endpoint normalization
    # ---------------------------
    def _normalize_endpoints(self, plan: dict) -> List[dict]:
        endpoints = list(plan.get("endpoints", []))

        # fallback als plan leeg is
        if not endpoints:
            endpoints = [
                {"method": "GET", "path": "/"},
                {"method": "GET", "path": "/health"}
            ]

        # altijd health toevoegen
        if not any(ep.get("path") == "/health" for ep in endpoints):
            endpoints.append({
                "method": "GET",
                "path": "/health",
                "expected_status": 200
            })

        return endpoints

    # ---------------------------
    # Stateful resource tracking
    # ---------------------------
    def _extract_id(self, response) -> Any:
        try:
            data = response.json()
            if isinstance(data, dict):
                for key in ["id", "todo_id", "item_id"]:
                    if key in data:
                        return data[key]
        except Exception:
            pass
        return None

    def _inject_path_params(self, path: str, state: dict) -> str:
        if not state.get("id"):
            return path
    # vervang elke {xxx_id} of {id} of {item_id} placeholder met de gevangen id
        return re.sub(r"\{[^}]*id[^}]*\}", str(state["id"]), path, flags=re.IGNORECASE)

    # ---------------------------
    # Main service tester
    # ---------------------------
    def _run_service_tests(self, plan: dict, image_tag: str, port: int) -> dict:
        container = f"functest-{plan['project_name']}"
        base_url = f"http://127.0.0.1:{port}"

        # start
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

        # readiness
        if not self._wait_ready(base_url):
            logs = self._logs(container)
            self._cleanup(container)
            return {
                "passed": False,
                "scenarios_run": 0,
                "results": [{
                    "scenario": {"name": "service readiness"},
                    "evaluation": {"passed": False, "reasons": ["not ready"]},
                    "run": {"stdout": logs, "stderr": ""}
                }]
            }

        endpoints = self._normalize_endpoints(plan)

        results = []
        state = {}
        all_passed = True

        with httpx.Client(timeout=5.0) as client:
            try:
                for ep in endpoints:
                    method = ep.get("method", "GET").upper()
                    raw_path = ep.get("path", "/")
                    path = self._inject_path_params(raw_path, state)
                    url = base_url + path
                    body = ep.get("request_example")
                    # GET met request_example: stuur als query string, niet als JSON body
                    if method == "GET" and body and isinstance(body, dict):
                        qs = {k: v for k, v in body.items() if v is not None}
                        if qs:
                            url = f"{url}?{urlencode(qs)}"
                        body = None
                    expected = self._infer_expected_status(ep)

                    try:
                        r = self._request(client, method, url, json_body=body)

                        status = r.status_code
                        text = r.text[:500]

                        if "expected_status" in ep:
                            passed = status == expected
                            reasons = [] if passed else [f"expected {expected}, got {status}"]
                        else:
                            passed = 200 <= status < 300
                            reasons = [] if passed else [f"got {status} (expected 2xx)"]

                        # capture id
                        if method == "POST" and passed:
                            new_id = self._extract_id(r)
                            if new_id:
                                state["id"] = new_id

                        logs = "" if passed else self._logs(container)

                        if not passed:
                            all_passed = False
                            print(f"[FAIL] {method} {path} → {status}")
                        else:
                            print(f"[ OK ] {method} {path} → {status}")

                        results.append({
                            "scenario": {"name": f"{method} {raw_path}"},
                            "run": {
                                "stdout": text,
                                "stderr": logs,
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
                        logs = self._logs(container)

                        results.append({
                            "scenario": {"name": f"{method} {raw_path}"},
                            "run": {
                                "stdout": "",
                                "stderr": str(e) + "\n" + logs,
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

    # ---------------------------
    # Entry point
    # ---------------------------
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

        # fallback CLI (minimal, deterministic)
        print("\n[functional] CLI test")

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
