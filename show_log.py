#!/usr/bin/env python3
"""Toon een run log overzichtelijk. Gebruik: python show_log.py [pad-naar-log.json]"""
import sys
import json
from pathlib import Path

if len(sys.argv) > 1:
    log_path = Path(sys.argv[1])
else:
    # Pak laatste log
    logs = sorted(Path("logs").glob("run_*.json"))
    if not logs:
        print("Geen logs gevonden")
        sys.exit(1)
    log_path = logs[-1]

print(f"=== {log_path.name} ===\n")
log = json.loads(log_path.read_text())

print(f"Taak: {log['task'][:80]}...")
print(f"Status: {log.get('status', 'unknown')}")
print(f"Plan: {log.get('plan', {}).get('project_name', 'n/a')}")
print()

for attempt_key, attempt_data in log.get("attempts", {}).items():
    print(f"--- {attempt_key} ---")
    print(f"  developer: {attempt_data.get('developer_duration', 0):.1f}s")
    print(f"  builder:   {attempt_data.get('builder_duration', 0):.3f}s")
    print(f"  tester:    {attempt_data.get('tester_duration', 0):.1f}s -> passed={attempt_data.get('tests_passed', 'n/a')}")

    if attempt_data.get("failed_steps"):
        for fs in attempt_data["failed_steps"]:
            print(f"  ✗ {fs['name']} (exit {fs['exit_code']})")
            if fs.get("stderr_tail"):
                print(f"    stderr: ...{fs['stderr_tail'][-200:]}")
            if fs.get("stdout_tail"):
                print(f"    stdout: ...{fs['stdout_tail'][-200:]}")

    if "verdict" in attempt_data:
        print(f"  judge: {attempt_data['verdict']}")
    print()
