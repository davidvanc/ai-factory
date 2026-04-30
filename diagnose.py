#!/usr/bin/env python3
"""Diagnostiek tool: draai de Tester opnieuw op een bestaand project en toon alle output."""
import sys
import json
from pathlib import Path
from src.agents.tester import TesterAgent

if len(sys.argv) != 2:
    print("Gebruik: python diagnose.py output/project_naam")
    sys.exit(1)

project_path = sys.argv[1]
build_result = {
    "project_path": project_path,
    "is_web_app": False
}

print(f"[diagnose] tester runnen op {project_path}")
result = TesterAgent().run(build_result)

print("\n=== VOLLEDIGE OUTPUT ===")
for step in result.get("steps", []):
    print(f"\n--- {step.get('name')} (ok={step.get('ok')}) ---")
    print("STDOUT:", step.get("stdout", "")[-1500:])
    print("STDERR:", step.get("stderr", "")[-1500:])

print(f"\nEindresultaat: passed={result.get('passed')}")
