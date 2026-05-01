"""
De factory pipeline als één aanroepbare functie - voor RQ workers.
"""
import json
import time
from datetime import datetime
from pathlib import Path


def run_factory_pipeline(task: str, max_tester_attempts: int = 6,
                          max_judge_attempts: int = 3) -> dict:
    """
    Voer de complete factory pipeline uit op één taak.
    Returns: dict met status en resultaten.
    """
    from src.agents.planner import PlannerAgent
    from src.agents.developer import DeveloperAgent
    from src.agents.builder import BuilderAgent
    from src.agents.tester import TesterAgent
    from src.agents.judge import JudgeAgent
    from src.llm.memory_client import MemoryClient

    no_progress_threshold = 2

    Path("logs").mkdir(exist_ok=True)
    log_file = Path("logs") / f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    run_log = {"task": task, "start": datetime.now().isoformat(), "attempts": {}}

    def count_passing(test_result):
        import re
        for step in test_result.get("steps", []):
            if step.get("name") == "pytest":
                m = re.search(r"(\d+) passed", step.get("stdout", ""))
                if m:
                    return int(m.group(1))
        return 0

    def build_feedback(test_result, verdict, prev_dev=None):
        issues = []
        test_output = ""
        for step in test_result.get("steps", []):
            if not step.get("ok", True):
                issues.append(f"{step['name']}: {step.get('stderr', '')[:200]}")
                test_output += f"\n--- {step['name']} ---\n{step.get('stdout', '')}\n{step.get('stderr', '')}"
        for criterion in ["functional_match", "security", "documentation", "code_quality"]:
            c = verdict.get(criterion, {})
            if not c.get("pass", True):
                issues.append(f"{criterion}: {c.get('reason', '')}")
        fb = {
            "summary": verdict.get("verdict_reason", "Tests of judge faalden"),
            "issues": issues,
            "test_output": test_output[-3000:]
        }
        if prev_dev:
            fb["previous_files"] = prev_dev.get("files", [])
        return fb

    try:
        # PLANNER
        plan = PlannerAgent().run(task)
        run_log["plan"] = plan
        project_name = plan["project_name"]

        feedback = None
        approved = False
        last_build = None
        last_verdict = None
        dev_result = None
        attempt = 0
        passing_history = []
        no_progress = 0
        tests_ok = False

        # FASE 1: Tester loop
        for ta in range(1, max_tester_attempts + 1):
            attempt = ta
            run_log["attempts"][f"attempt_{attempt}"] = {"phase": "tester"}
            use_premium = (ta == max_tester_attempts)
            role = "developer_premium" if use_premium else "developer"

            t0 = time.time()
            dev_result = DeveloperAgent().run(plan, feedback=feedback, role_override=role)
            run_log["attempts"][f"attempt_{attempt}"]["dev_duration"] = time.time() - t0
            run_log["attempts"][f"attempt_{attempt}"]["model"] = role

            t0 = time.time()
            build_result = BuilderAgent().run(plan, dev_result, attempt=attempt)
            run_log["attempts"][f"attempt_{attempt}"]["build_duration"] = time.time() - t0
            last_build = build_result

            t0 = time.time()
            test_result = TesterAgent().run(build_result)
            run_log["attempts"][f"attempt_{attempt}"]["test_duration"] = time.time() - t0
            run_log["attempts"][f"attempt_{attempt}"]["tests_passed"] = test_result["passed"]

            passing = count_passing(test_result)
            passing_history.append(passing)
            run_log["attempts"][f"attempt_{attempt}"]["passing_count"] = passing

            if not test_result["passed"]:
                if len(passing_history) >= 2 and passing_history[-1] <= passing_history[-2]:
                    no_progress += 1
                feedback = build_feedback(test_result, {"verdict_reason": "Tests failed"}, dev_result)
                continue

            tests_ok = True

            t0 = time.time()
            verdict = JudgeAgent().run(plan, build_result, test_result)
            run_log["attempts"][f"attempt_{attempt}"]["judge_duration"] = time.time() - t0
            run_log["attempts"][f"attempt_{attempt}"]["verdict"] = verdict.get("overall_verdict")
            last_verdict = verdict

            if verdict.get("overall_verdict") == "APPROVED":
                approved = True
                break

            feedback = build_feedback(test_result, verdict, dev_result)
            break  # tests OK, ga naar fase 2

        # FASE 2: Judge loop
        if tests_ok and not approved:
            for ja in range(1, max_judge_attempts + 1):
                attempt += 1
                run_log["attempts"][f"attempt_{attempt}"] = {"phase": "judge_fix"}
                use_premium = (ja == max_judge_attempts)
                role = "developer_premium" if use_premium else "developer"

                dev_result = DeveloperAgent().run(plan, feedback=feedback, role_override=role)
                build_result = BuilderAgent().run(plan, dev_result, attempt=attempt)
                last_build = build_result
                test_result = TesterAgent().run(build_result)

                if not test_result["passed"]:
                    feedback = build_feedback(test_result, {"verdict_reason": "Tests failed"}, dev_result)
                    continue

                verdict = JudgeAgent().run(plan, build_result, test_result)
                last_verdict = verdict
                run_log["attempts"][f"attempt_{attempt}"]["verdict"] = verdict.get("overall_verdict")

                if verdict.get("overall_verdict") == "APPROVED":
                    approved = True
                    break

                feedback = build_feedback(test_result, verdict, dev_result)

        # Resultaat
        status = "success" if approved else "failed"
        run_log["status"] = status
        run_log["final_attempt"] = attempt
        run_log["end"] = datetime.now().isoformat()
        log_file.write_text(json.dumps(run_log, indent=2, default=str))

        # Git push met retry-loop (race condition bescherming)
        if approved:
            try:
                _push_to_git(project_name, attempt)
            except Exception as e:
                print(f"[git] push faalde definitief: {e}")

        # Memory bijwerken
        try:
            memory = MemoryClient()
            memory.add_project(
                project_name=plan.get("project_name", "unknown"),
                task=task,
                description=plan.get("description", ""),
                status=status,
                attempts=attempt,
                premium_used=any(a.get("model") == "developer_premium"
                                 for a in run_log["attempts"].values()),
                metadata={"final_attempt": attempt, "log_file": str(log_file)}
            )
        except Exception as e:
            print(f"[memory] {e}")

        return {
            "status": status,
            "project_name": project_name,
            "project_path": last_build["project_path"] if last_build else None,
            "attempts": attempt,
            "approved": approved,
            "log_file": str(log_file)
        }

    except Exception as e:
        run_log["status"] = "error"
        run_log["error"] = str(e)
        run_log["end"] = datetime.now().isoformat()
        log_file.write_text(json.dumps(run_log, indent=2, default=str))
        return {"status": "error", "error": str(e), "log_file": str(log_file)}
def _push_to_git(project_name: str, attempt: int, max_retries: int = 5):
    """Push gegenereerde output naar GitHub met retry bij race conditions."""
    import subprocess
    import time

    for retry in range(max_retries):
        try:
            # Eerst pullen om eventuele andere worker-pushes binnen te halen
            subprocess.run(["git", "pull", "--rebase", "--autostash"],
                         check=True, capture_output=True, timeout=30)

            # Add het project
            subprocess.run(["git", "add", f"output/{project_name}"],
                         check=True, capture_output=True, timeout=10)

            # Commit (kan falen als nothing to commit)
            commit_result = subprocess.run(
                ["git", "commit", "-m", f"factory output: {project_name} (poging {attempt})"],
                capture_output=True, text=True, timeout=10
            )
            if commit_result.returncode != 0 and "nothing to commit" in commit_result.stdout.lower():
                print(f"[git] geen wijzigingen voor {project_name}")
                return

            # Push
            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True, text=True, timeout=60
            )

            if push_result.returncode == 0:
                print(f"[git] {project_name} succesvol gepusht (poging {retry + 1})")
                return

            # Push faalde — waarschijnlijk race condition
            print(f"[git] push poging {retry + 1} faalde, retry...")
            time.sleep(2 ** retry)  # exponential backoff: 1s, 2s, 4s, 8s, 16s

        except subprocess.TimeoutExpired:
            print(f"[git] timeout op poging {retry + 1}")
            time.sleep(2 ** retry)
        except subprocess.CalledProcessError as e:
            print(f"[git] poging {retry + 1} fout: {e.stderr.decode() if e.stderr else e}")
            time.sleep(2 ** retry)

    raise Exception(f"Git push faalde na {max_retries} pogingen")
