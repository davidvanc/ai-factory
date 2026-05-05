import subprocess
import time
from pathlib import Path
import json

class TesterAgent:
    def __init__(self):
        pass

    def _run(self, cmd: list, cwd: Path = None, timeout: int = 300) -> dict:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "ok": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"exit_code": -1, "stdout": "", "stderr": "TIMEOUT", "ok": False}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e), "ok": False}

    def run(self, build_result: dict, plan: dict = None) -> dict:
        project_path = Path(build_result["project_path"])
        project_name = project_path.name
        is_web_app = build_result.get("is_web_app", False)
        image_tag = f"ai-factory/{project_name}:test"
        container_name = f"ai-factory-test-{project_name}"

        results = {"project": project_name, "steps": [], "passed": False}

        # === STAP 1: Docker build ===
        print(f"\n[tester] 1/3 docker build {image_tag}...")
        build = self._run(
            ["docker", "build", "-t", image_tag, "."],
            cwd=project_path,
            timeout=600
        )
        results["steps"].append({"name": "docker_build", **build})
        if not build["ok"]:
            print("[tester] FAIL: docker build")
            print(build["stderr"][-500:])
            return results
        print("[tester] docker build OK")

        # === STAP 2: pytest in container ===
        print("[tester] 2/3 pytest...")
        test = self._run(
            ["docker", "run", "--rm", "--entrypoint", "", image_tag,
             "python", "-m", "pytest", "tests/", "-v", "-p", "no:cacheprovider"],
            timeout=300
        )
        results["steps"].append({"name": "pytest", **test})
        if not test["ok"]:
            print("[tester] FAIL: pytest")
            print(test["stdout"][-800:])
            return results
        print("[tester] pytest OK")

        # === STAP 3: Runtime startup test ===
        print("[tester] 3/3 runtime startup test...")
        # Cleanup eventuele oude container
        self._run(["docker", "rm", "-f", container_name])

        if is_web_app:
            # Web app: start in achtergrond, wacht 5 sec, check of hij draait
            start = self._run(
                ["docker", "run", "-d", "--name", container_name, image_tag],
                timeout=30
            )
            if not start["ok"]:
                results["steps"].append({"name": "runtime", **start})
                print("[tester] FAIL: container start")
                return results

            time.sleep(5)

            # Check status
            status = self._run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_name]
            )
            logs = self._run(["docker", "logs", container_name])

            self._run(["docker", "stop", container_name], timeout=10)
            self._run(["docker", "rm", "-f", container_name])

            running = "running" in status["stdout"]
            results["steps"].append({
                "name": "runtime",
                "ok": running,
                "stdout": logs["stdout"][-500:],
                "stderr": logs["stderr"][-500:]
            })
            if not running:
                print("[tester] FAIL: container niet running")
                print("logs:", logs["stdout"][-500:])
                return results
            print("[tester] runtime OK (container draait stabiel)")

        else:
            # CLI tool: gewoon laten draaien en check exit code (mag 0 of >0 zijn,
            # zolang het geen ImportError of SyntaxError is)
            start = self._run(
                ["docker", "run", "--rm", "--name", container_name, image_tag],
                timeout=30
            )
            stderr = start["stderr"].lower()
            crashed_on_import = (
                "modulenotfounderror" in stderr or
                "importerror" in stderr or
                "syntaxerror" in stderr
            )
            results["steps"].append({
                "name": "runtime",
                "ok": not crashed_on_import,
                "stdout": start["stdout"][-500:],
                "stderr": start["stderr"][-500:]
            })
            if crashed_on_import:
                print("[tester] FAIL: import/syntax fout bij runtime")
                print(start["stderr"][-500:])
                return results
            print("[tester] runtime OK (geen import/syntax fouten)")
        # === STAP 4: Functional smoke test ===
        if plan is not None:
            print("[tester] 4/4 functional smoke test...")
            try:
                from src.agents.functional_tester import FunctionalTester
                func_result = FunctionalTester().run(plan, build_result)
                results["steps"].append({
                    "name": "functional",
                    "ok": func_result["passed"],
                    "stdout": json.dumps(func_result.get("results", []))[:1500],
                    "stderr": ""
                })
                if not func_result["passed"]:
                    print("[tester] FAIL: functional smoke test")
                    return results
                print(f"[tester] functional OK ({func_result['scenarios_run']} scenarios)")
            except Exception as e:
                print(f"[tester] functional test crashed: {e}")
                results["steps"].append({
                    "name": "functional",
                    "ok": False,
                    "stdout": "",
                    "stderr": str(e)
                })
                return results

        results["passed"] = True
        return results
