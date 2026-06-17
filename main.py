#!/usr/bin/env python3
"""
AI Software Factory — lokale orchestrator.

Eén machine, één commando, geen queue en geen aparte VM's:

    python main.py "Maak een service die hex-kleuren naar RGB omzet"

De volledige pipeline (Planner -> Developer -> Builder -> Tester -> Judge ->
git push) draait synchroon in dit proces via run_factory_pipeline().
"""
import argparse
import json
import sys
from pathlib import Path

from src.workflow.pipeline import run_factory_pipeline


def load_input_context(input_dir: Path) -> str:
    """Lees optionele extra-context bestanden uit de input/ map."""
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


def main():
    parser = argparse.ArgumentParser(description="AI Software Factory (lokaal)")
    parser.add_argument("task", help="Taakomschrijving voor het systeem")
    parser.add_argument("--input", default="input", help="Map met extra context bestanden")
    parser.add_argument("--max-tester-attempts", type=int, default=6,
                        help="Max aantal Developer->Tester pogingen (laatste = premium model)")
    parser.add_argument("--max-judge-attempts", type=int, default=3,
                        help="Max aantal pogingen om Judge-approval te halen")
    args = parser.parse_args()

    full_task = args.task
    context = load_input_context(Path(args.input))
    if context:
        print(f"[orchestrator] {len(context)} chars context ingeladen uit {args.input}/")
        full_task = f"{args.task}\n\nExtra context uit input/ map:\n{context}"

    result = run_factory_pipeline(
        full_task,
        max_tester_attempts=args.max_tester_attempts,
        max_judge_attempts=args.max_judge_attempts,
    )

    print("\n" + "=" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print("=" * 70)

    status = result.get("status")
    if status == "success":
        print(f"\nSUCCES — project staat in: {result.get('project_path')}")
        sys.exit(0)
    elif status == "error":
        print(f"\nFOUT: {result.get('error')}  (log: {result.get('log_file')})")
        sys.exit(1)
    else:
        print(f"\nGEFAALD na {result.get('attempts')} pogingen  (log: {result.get('log_file')})")
        sys.exit(1)


if __name__ == "__main__":
    main()
