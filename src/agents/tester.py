import subprocess
from pathlib import Path

class TesterAgent:
    def __init__(self):
        pass

    def _run(self, cmd: list, cwd: Path, timeout: int = 300) -> dict:
        """Voer een shell commando uit en vang stdout/stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
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

    def run(self, build_result: dict) -> dict:
        project_path = Path(build_result["project_path"])
        project_name = project_path.name
        image_tag = f"ai-factory/{project_name}:test"

        results = {
            "project": project_name,
            "steps": [],
            "passed": False
        }

        # Stap 1: Docker image bouwen
        print(f"[tester] bouwen van Docker image {image_tag}...")
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

        # Stap 2: Tests draaien in de container
        print("[tester] tests draaien...")
        test_run = self._run(
            ["docker", "run", "--rm", "--entrypoint", "", image_tag,
             "python", "-m", "pytest", "tests/", "-v"],
            cwd=project_path,
            timeout=300
        )
        results["steps"].append({"name": "pytest", **test_run})

        if test_run["ok"]:
            print("[tester] alle tests slagen")
            results["passed"] = True
        else:
            print("[tester] FAIL: tests")
            print(test_run["stdout"][-800:])
            print(test_run["stderr"][-300:])

        return results
