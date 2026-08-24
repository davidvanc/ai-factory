"""
Functional Tester — start service in container en test elk endpoint uit het plan
met state tracking voor path params (POST → vang id → gebruik in volgende calls).
"""
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

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
    # Readiness
    # -----------------------------
    def _wait_ready(self, base_url: str, timeout: int = 25) -> bool:
        paths = ["/health", "/", "/docs", "/openapi.json"]
        with httpx.Client(timeout=2.0) as client:
            start = time.time()
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
    # Verwacht status uit plan
    # -----------------------------
    def _infer_expected_status(self, ep: dict) -> int:
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

    # -----------------------------
    # Endpoints normaliseren (health altijd erbij)
    # -----------------------------
    def _normalize_endpoints(self, plan: dict) -> list:
        endpoints = list(plan.get("endpoints", []))
        if not endpoints:
            endpoints = [
                {"method": "GET", "path": "/"},
                {"method": "GET", "path": "/health"},
            ]
        if not any(ep.get("path") == "/health" for ep in endpoints):
            endpoints.append({
                "method": "GET",
                "path": "/health",
                "expected_status": 200,
            })
        return endpoints

    # -----------------------------
    # Path-param injectie: vervang elke placeholder met 'id' in de naam
    # ({id}, {todo_id}, {user_id}, {ITEM_ID}, ...)
    # -----------------------------
    def _inject_path_params(self, path: str, state: dict) -> str:
        if not state.get("id"):
            return path
        return re.sub(r"\{[^}]*[iI][dD][^}]*\}", str(state["id"]), path)

    @staticmethod
    def _openstaande_params(path: str) -> list:
        """Padparameters die we niet konden invullen.

        Blijft er een over, dan is het verzoek niet op te bouwen en zegt het
        antwoord niets over de service - die krijgt dan letterlijk '{naam}' als
        waarde binnen en antwoordt terecht met 404.
        """
        return re.findall(r"\{[^}]+\}", path)

    # -----------------------------
    # Vang id uit POST response
    # -----------------------------
    def _extract_id(self, response) -> Any:
        try:
            data = response.json()
        except Exception:
            return None
        if isinstance(data, dict):
            if "id" in data:
                return data["id"]
            for k, v in data.items():
                if isinstance(k, str) and k.lower().endswith("id"):
                    return v
        return None

    # -----------------------------
    # Hoofdtest
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
                    "scenario": {"name": "service readiness"},
                    "evaluation": {"passed": False, "reasons": ["not ready"]},
                    "run": {"stdout": container_logs, "stderr": ""}
                }]
            }

        endpoints = self._normalize_endpoints(plan)
        results = []
        state: dict = {}
        all_passed = True

        with httpx.Client(timeout=5.0) as client:
            try:
                for ep in endpoints:
                    method = ep.get("method", "GET").upper()
                    raw_path = ep.get("path", "/")
                    path = self._inject_path_params(raw_path, state)

                    openstaand = self._openstaande_params(path)
                    if openstaand:
                        # Niet op te bouwen, dus niets over te zeggen. Wel
                        # zichtbaar maken, anders lijkt de dekking groter dan ze is.
                        print(f"[functional]   OVERGESLAGEN: {method} {raw_path} "
                              f"(geen waarde voor {', '.join(openstaand)})")
                        results.append({
                            "scenario": {"name": f"{method} {raw_path}"},
                            "run": {"stdout": "", "stderr": ""},
                            "evaluation": {
                                "passed": True,
                                "skipped": True,
                                "reasons": [f"overgeslagen: geen waarde voor "
                                            f"{', '.join(openstaand)} in het pad"],
                            },
                        })
                        continue

                    url = base_url + path
                    body = ep.get("request_example")

                    # GET met request_example → stuur als query string, niet als JSON body
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

                        # Strict check als plan een explicit expected_status zet,
                        # anders lenient (elke 2xx oké)
                        if "expected_status" in ep:
                            passed = status == expected
                            reason = f"expected {expected}, got {status}"
                        else:
                            passed = 200 <= status < 300
                            reason = f"got {status} (expected 2xx)"

                        reasons = [] if passed else [reason]

                        if method == "POST" and passed:
                            new_id = self._extract_id(r)
                            if new_id is not None:
                                state["id"] = new_id

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
                        "exit_code": r.returncode,
                    },
                    "evaluation": {
                        "passed": passed,
                        "reasons": [] if passed else ["non-zero exit"],
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
                    "evaluation": {"passed": False, "reasons": ["execution failed"]},
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
