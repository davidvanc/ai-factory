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

MAX_ATTEMPTS = 3


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


def build_feedback(test_result: dict, judge_verdict: dict) -> dict:
    """Bundel feedback voor de Developer in de volgende poging."""
    issues = []
    test_output = ""

    # Verzamel test failures
    for step in test_result.get("steps", []):
        if not step.get("ok", True):
            issues.append(f"{step['name']} faalde: {step.get('stderr', '')[:200]}")
            test_output += f"\n--- {step['name']} ---\n{step.get('stdout', '')}\n{step.get('stderr', '')}"

    # Verzamel judge issues
    for criterion in ["functional_match", "security", "documentation", "code_quality"]:
        c = judge_verdict.get(criterion, {})
        if not c.get("pass", True):
            issues.append(f"{criterion}: {c.get('reason', '')}")

    summary = judge_verdict.get("verdict_reason", "Tests of judge faalden")

    return {
        "summary": summary,
        "issues": issues,
        "test_output": test_output[-2000:]  # laatste 2000 chars
    }


def run_pipeline(plan: dict, feedback: dict, attempt: int, args, run_log: dict):
    """Eén poging van Developer → Builder → Tester → Judge."""

    banner(f"POGING {attempt}/{MAX_ATTEMPTS} — Developer")
    t0 = time.time()
    dev_result = DeveloperAgent().run(plan, feedback=feedback)
    run_log["attempts"][f"attempt_{attempt}"]["developer_duration"] = time.time() - t0

    banner(f"POGING {attempt}/{MAX_ATTEMPTS} — Builder")
    t0 = time.time()
    build_result = BuilderAgent().run(plan, dev_result, attempt=attempt)
    run_log["attempts"][f"attempt_{attempt}"]["builder_duration"] = time.time() - t0

    test_result = {"passed": True, "steps": []}
    if not args.skip_test:
        banner(f"POGING {attempt}/{MAX_ATTEMPTS} — Tester")
        t0 = time.time()
        test_result = TesterAgent().run(build_result)
        run_log["attempts"][f"attempt_{attempt}"]["tester_duration"] = time.time() - t0
        run_log["attempts"][f"attempt_{attempt}"]["tests_passed"] = test_result["passed"]

        # Sla gedetailleerde failure info op
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

        if not test_result["passed"]:
            return False, build_result, test_result, {"verdict_reason": "Tests failed"}

        # NIEUW: gedetailleerde failure info
        if not test_result["passed"]:
            failed_steps = []
            for step in test_result.get("steps", []):
                if not step.get("ok", True):
                    failed_steps.append({
                        "name": step.get("name"),
                        "exit_code": step.get("exit_code"),
                        "stderr_tail": step.get("stderr", "")[-500:],
                        "stdout_tail": step.get("stdout", "")[-500:]
                    })
            run_log["attempts"][f"attempt_{attempt}"]["failed_steps"] = failed_steps

        if not test_result["passed"]:
            return False, build_result, test_result, {"verdict_reason": "Tests failed"}

    banner(f"POGING {attempt}/{MAX_ATTEMPTS} — Judge")
    t0 = time.time()
    verdict = JudgeAgent().run(plan, build_result, test_result)
    run_log["attempts"][f"attempt_{attempt}"]["judge_duration"] = time.time() - t0
    run_log["attempts"][f"attempt_{attempt}"]["verdict"] = verdict.get("overall_verdict")

    print(f"\n[judge] {verdict.get('overall_verdict')}: {verdict.get('verdict_reason', '')}")

    approved = verdict.get("overall_verdict") == "APPROVED"
    return approved, build_result, test_result, verdict


def main():
    parser = argparse.ArgumentParser(description="AI Software Factory")
    parser.add_argument("task", help="Taakomschrijving voor het systeem")
    parser.add_argument("--input", default="input", help="Map met extra context bestanden")
    parser.add_argument("--skip-test", action="store_true", help="Sla de Docker tests over")
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS, help="Max aantal retry-pogingen")
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
        feedback = None
        approved = False
        last_build_result = None
        last_verdict = None

        for attempt in range(1, args.max_attempts + 1):
            run_log["attempts"][f"attempt_{attempt}"] = {}
            approved, build_result, test_result, verdict = run_pipeline(
                plan, feedback, attempt, args, run_log
            )
            last_build_result = build_result
            last_verdict = verdict

            if approved:
                break

            # Bouw feedback voor volgende poging
            if attempt < args.max_attempts:
                feedback = build_feedback(test_result, verdict)
                print(f"\n[orchestrator] poging {attempt} faalde, retry met feedback...")
                print(f"[orchestrator] {len(feedback['issues'])} issues om op te lossen")

        # Eindresultaat
        if approved:
            banner("RESULTAAT: SUCCES")
            print(f"Project staat in: {last_build_result['project_path']}")
            print(f"Geslaagd na poging: {attempt}/{args.max_attempts}")
            run_log["status"] = "success"
            run_log["final_attempt"] = attempt
        else:
            banner(f"RESULTAAT: GEFAALD NA {args.max_attempts} POGINGEN")
            print("Laatste verdict:")
            print(json.dumps(last_verdict, indent=2, ensure_ascii=False))
            run_log["status"] = "max_attempts_exceeded"
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


def _save_log(path: Path, log: dict):
    log["end"] = datetime.now().isoformat()
    path.write_text(json.dumps(log, indent=2, default=str))


if __name__ == "__main__":
    main()
