#!/usr/bin/env python3
"""
AI Software Factory - Orchestrator met self-healing retry-loop
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from src.agents.planner import PlannerAgent
from src.agents.developer import DeveloperAgent
from src.agents.builder import BuilderAgent
from src.agents.tester import TesterAgent
from src.agents.judge import JudgeAgent
from src.llm.memory_client import MemoryClient

MAX_TESTER_ATTEMPTS = 6      # 5 normaal + 1 premium
MAX_JUDGE_ATTEMPTS = 3        # 2 normaal + 1 premium
NO_PROGRESS_THRESHOLD = 2     # stop als 2x geen verbetering


def banner(text: str):
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)


def load_input_context(input_dir: Path) -> str:
    if not input_dir.exists():
        return ""
    parts = []
    for f in sorted(input_dir.rglob("*")):
        if f.is_file() and f.suffix in [".md", ".txt", ".csv", ".json"]:
            try:
                content = f.read_text()
                parts.append(f"--- Bestand: {f.relative_to(input_dir)} ---\n{content}\n")
            except Exception:
                pass
    return "\n".join(parts)


def build_feedback(test_result: dict, judge_verdict: dict, previous_dev_result: dict = None) -> dict:
    """Bundel feedback inclusief de vorige code voor de Developer in de volgende poging."""
    issues = []
    test_output = ""

    for step in test_result.get("steps", []):
        if not step.get("ok", True):
            issues.append(f"{step['name']} faalde: {step.get('stderr', '')[:200]}")
            test_output += f"\n--- {step['name']} ---\n{step.get('stdout', '')}\n{step.get('stderr', '')}"

    for criterion in ["functional_match", "security", "documentation", "code_quality"]:
        c = judge_verdict.get(criterion, {})
        if not c.get("pass", True):
            issues.append(f"{criterion}: {c.get('reason', '')}")

    summary = judge_verdict.get("verdict_reason", "Tests of judge faalden")

    feedback = {
        "summary": summary,
        "issues": issues,
        "test_output": test_output[-3000:]
    }

    if previous_dev_result:
        feedback["previous_files"] = previous_dev_result.get("files", [])

    return feedback

def _count_passing_tests(test_result: dict) -> int:
    """Tel hoeveel tests slaagden in pytest output."""
    for step in test_result.get("steps", []):
        if step.get("name") == "pytest":
            stdout = step.get("stdout", "")
            # Zoek naar pytest summary regel zoals "5 passed" of "3 passed, 2 failed"
            import re
            m = re.search(r"(\d+) passed", stdout)
            if m:
                return int(m.group(1))
    return 0


def run_pipeline(plan: dict, feedback: dict, attempt: int, args, run_log: dict, use_premium: bool = False):
    """Eén poging van Developer → Builder → Tester → Judge."""

    role = "developer_premium" if use_premium else "developer"
    label = f"POGING {attempt}" + (" [PREMIUM]" if use_premium else "")

    banner(f"{label} — Developer ({role})")
    t0 = time.time()
    dev_result = DeveloperAgent().run(plan, feedback=feedback, role_override=role)
    run_log["attempts"][f"attempt_{attempt}"]["developer_duration"] = time.time() - t0
    run_log["attempts"][f"attempt_{attempt}"]["model"] = role

    banner(f"{label} — Builder")
    t0 = time.time()
    build_result = BuilderAgent().run(plan, dev_result, attempt=attempt)
    run_log["attempts"][f"attempt_{attempt}"]["builder_duration"] = time.time() - t0

    test_result = {"passed": True, "steps": []}
    if not args.skip_test:
        banner(f"{label} — Tester")
        t0 = time.time()
        test_result = TesterAgent().run(build_result)
        run_log["attempts"][f"attempt_{attempt}"]["tester_duration"] = time.time() - t0
        run_log["attempts"][f"attempt_{attempt}"]["tests_passed"] = test_result["passed"]
        run_log["attempts"][f"attempt_{attempt}"]["passing_count"] = _count_passing_tests(test_result)

        if not test_result["passed"]:
            failed_steps = []
            for step in test_result.get("steps", []):
                if not step.get("ok", True):
                    failed_steps.append({
                        "name": step.get("name"),
                        "exit_code": step.get("exit_code"),
                        "stderr_tail": step.get("stderr", "")[-800:],
                        "stdout_tail": step.get("stdout", "")[-800:]
                    })
            run_log["attempts"][f"attempt_{attempt}"]["failed_steps"] = failed_steps
            return False, build_result, test_result, {"verdict_reason": "Tests failed"}, dev_result

    banner(f"{label} — Judge")
    t0 = time.time()
    verdict = JudgeAgent().run(plan, build_result, test_result)
    run_log["attempts"][f"attempt_{attempt}"]["judge_duration"] = time.time() - t0
    run_log["attempts"][f"attempt_{attempt}"]["verdict"] = verdict.get("overall_verdict")

    print(f"\n[judge] {verdict.get('overall_verdict')}: {verdict.get('verdict_reason', '')}")

    approved = verdict.get("overall_verdict") == "APPROVED"
    return approved, build_result, test_result, verdict, dev_result

def main():
    parser = argparse.ArgumentParser(description="AI Software Factory")
    parser.add_argument("task", help="Taakomschrijving voor het systeem")
    parser.add_argument("--input", default="input", help="Map met extra context bestanden")
    parser.add_argument("--skip-test", action="store_true", help="Sla de Docker tests over")
    parser.add_argument("--max-attempts", type=int, default=MAX_TESTER_ATTEMPTS, help="Max aantal retry-pogingen")
    args = parser.parse_args()

    Path("logs").mkdir(exist_ok=True)
    log_file = Path("logs") / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    run_log = {
        "task": args.task,
        "start": datetime.now().isoformat(),
        "attempts": {}
    }

    context = load_input_context(Path(args.input))
    full_task = args.task
    if context:
        full_task = f"{args.task}\n\nExtra context uit input/ map:\n{context}"
        print(f"[orchestrator] {len(context)} chars context ingeladen")

    try:
        # Planner draait maar één keer
        banner("PLANNER")
        t0 = time.time()
        plan = PlannerAgent().run(full_task)
        run_log["plan"] = plan
        run_log["planner_duration"] = time.time() - t0
        print(f"\n[planner] project: {plan['project_name']}")

        # Retry-loop
        # Twee retry-fases:
        # FASE 1: Tester loop (max 6 pogingen, met forward-progress check)
        # FASE 2: Judge loop (max 3 pogingen om APPROVED te krijgen)

        feedback = None
        approved = False
        last_build_result = None
        last_verdict = None
        dev_result = None
        attempt = 0
        passing_history = []
        no_progress_count = 0
        tests_ok = False

        # FASE 1: Krijg de tests groen
        for tester_attempt in range(1, MAX_TESTER_ATTEMPTS + 1):
            attempt = tester_attempt
            run_log["attempts"][f"attempt_{attempt}"] = {"phase": "tester"}
            use_premium = (tester_attempt == MAX_TESTER_ATTEMPTS)

            tests_ok, build_result, test_result, verdict, dev_result = run_pipeline(
                plan, feedback, attempt, args, run_log, use_premium=use_premium
            )
            last_build_result = build_result
            last_verdict = verdict

            passing = run_log["attempts"][f"attempt_{attempt}"].get("passing_count", 0)
            passing_history.append(passing)

            if tests_ok:
                approved = (verdict.get("overall_verdict") == "APPROVED")
                if approved:
                    break
                # Tests OK maar Judge zei nee → ga naar fase 2
                feedback = build_feedback(test_result, verdict, previous_dev_result=dev_result)
                break

            # Tests faalden: check forward progress
            if len(passing_history) >= 2:
                if passing_history[-1] <= passing_history[-2]:
                    no_progress_count += 1
                else:
                    no_progress_count = 0
                print(f"\n[orchestrator] passing tests: {passing_history} (geen progress: {no_progress_count}x)")

                if no_progress_count >= NO_PROGRESS_THRESHOLD and not use_premium:
                    print(f"[orchestrator] {NO_PROGRESS_THRESHOLD}x geen progress — escalate naar premium model")
                    # Forceer next iteration premium
                    # (we doen dit door MAX_TESTER_ATTEMPTS-1 te bereiken)
                    if tester_attempt < MAX_TESTER_ATTEMPTS - 1:
                        # Skip naar de premium poging
                        for skip in range(tester_attempt + 1, MAX_TESTER_ATTEMPTS):
                            run_log["attempts"][f"attempt_{skip}"] = {"phase": "tester", "skipped": True}
                        attempt = MAX_TESTER_ATTEMPTS - 1

            feedback = build_feedback(test_result, verdict, previous_dev_result=dev_result)
            print(f"\n[orchestrator] tester poging {tester_attempt} faalde, retry...")

        # FASE 2: Als tests OK maar nog niet approved, krijg approval
        if tests_ok and not approved:
            print("\n[orchestrator] tests OK, nu Judge approval halen...")
            for judge_attempt in range(1, MAX_JUDGE_ATTEMPTS + 1):
                attempt += 1
                run_log["attempts"][f"attempt_{attempt}"] = {"phase": "judge_fix"}
                use_premium = (judge_attempt == MAX_JUDGE_ATTEMPTS)

                tests_ok, build_result, test_result, verdict, dev_result = run_pipeline(
                    plan, feedback, attempt, args, run_log, use_premium=use_premium
                )
                last_build_result = build_result
                last_verdict = verdict

                if tests_ok and verdict.get("overall_verdict") == "APPROVED":
                    approved = True
                    break

                feedback = build_feedback(test_result, verdict, previous_dev_result=dev_result)
        # Eindresultaat
        if approved:
            banner("RESULTAAT: SUCCES")
            print(f"Project staat in: {last_build_result['project_path']}")
            print(f"Geslaagd na poging: {attempt}/{args.max_attempts}")
            run_log["status"] = "success"
            run_log["final_attempt"] = attempt
            # Auto-commit naar Git
            print("\n[git] committen van gegenereerd project...")
            git_ok = _git_commit_output(
                last_build_result['project_path'],
                plan['project_name'],
                attempt
            )
            run_log["git_pushed"] = git_ok
            # Memory: opslaan in centrale store
            try:
                memory = MemoryClient()
                memory.add_project(
                    project_name=plan['project_name'],
                    task=args.task,
                    description=plan.get('description', ''),
                    status='success',
                    attempts=attempt,
                    premium_used=any(
                        a.get('model') == 'developer_premium'
                        for a in run_log.get('attempts', {}).values()
                    ),
                    metadata={'final_attempt': attempt}
                )
                print(f"[memory] project opgeslagen in centrale store")
            except Exception as e:
                print(f"[memory] opslaan faalde (niet kritiek): {e}")
        else:
            banner(f"RESULTAAT: GEFAALD NA {args.max_attempts} POGINGEN")
            print("Laatste verdict:")
            print(json.dumps(last_verdict, indent=2, ensure_ascii=False))
            run_log["status"] = "max_attempts_exceeded"
            try:
                memory = MemoryClient()
                memory.add_project(
                    project_name=plan.get('project_name', 'unknown'),
                    task=args.task,
                    description=plan.get('description', ''),
                    status='failed',
                    attempts=attempt,
                    metadata={'last_verdict': last_verdict}
                )
                # Lessen extraheren uit verdict
                if last_verdict and isinstance(last_verdict, dict):
                    for criterion in ['functional_match', 'security', 'documentation', 'code_quality']:
                        c = last_verdict.get(criterion, {})
                        if not c.get('pass', True) and c.get('reason'):
                            memory.add_lesson(
                                category=criterion,
                                pattern=c['reason'][:200]
                            )
            except Exception as e:
                print(f"[memory] opslaan faalde: {e}")
            _save_log(log_file, run_log)
            sys.exit(1)

        print(f"\nLogbestand: {log_file}")
        _save_log(log_file, run_log)

    except KeyboardInterrupt:
        print("\n[orchestrator] onderbroken door gebruiker")
        run_log["status"] = "interrupted"
        _save_log(log_file, run_log)
        sys.exit(130)
    except Exception as e:
        banner(f"FOUT: {type(e).__name__}")
        print(str(e))
        run_log["status"] = "error"
        run_log["error"] = str(e)
        _save_log(log_file, run_log)
        sys.exit(1)

def _git_commit_output(project_path: str, project_name: str, attempt: int):
    """Commit en push het gegenereerde project naar Git."""
    import subprocess
    try:
        # Add het project
        subprocess.run(["git", "add", project_path], check=True, cwd=".")

        # Commit met duidelijke message
        msg = f"factory output: {project_name} (poging {attempt})"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=".",
            capture_output=True,
            text=True
        )

        if result.returncode != 0 and "nothing to commit" in result.stdout.lower():
            print(f"[git] geen wijzigingen om te committen voor {project_name}")
            return True

        if result.returncode != 0:
            print(f"[git] commit faalde: {result.stderr[:200]}")
            return False

        # Push
        push = subprocess.run(
            ["git", "push"],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=60
        )
        if push.returncode != 0:
            print(f"[git] push faalde: {push.stderr[:200]}")
            return False

        print(f"[git] {project_name} succesvol gepusht naar GitHub")
        return True
    except subprocess.TimeoutExpired:
        print("[git] push timeout")
        return False
    except Exception as e:
        print(f"[git] onverwachte fout: {e}")
        return False

def _save_log(path: Path, log: dict):
    log["end"] = datetime.now().isoformat()
    path.write_text(json.dumps(log, indent=2, default=str))


if __name__ == "__main__":
    main()
