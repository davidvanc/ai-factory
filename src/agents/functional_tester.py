"""
Functional Tester — bedenkt en draait echte smoke tests op het gegenereerde project.
LLM bedenkt 2-3 realistische scenarios, runtime executeert ze, LLM oordeelt over output.
"""
import json
import subprocess
from pathlib import Path
from src.llm.client import LLMClient
from src.llm.json_utils import extract_json


class FunctionalTester:
    def __init__(self):
        self.llm = LLMClient()

    def _generate_scenarios(self, plan: dict, project_path: Path) -> list:
        """Vraag LLM om 2-3 realistische test scenarios voor dit project."""
        # Lees main.py om CLI structuur te begrijpen
        main_py = project_path / "src" / "main.py"
        main_content = main_py.read_text() if main_py.exists() else ""

        prompt = f"""Een Python project is net gebouwd. Genereer 2-3 SMOKE TESTS die het echt aanroepen.

Project: {plan['project_name']}
Beschrijving: {plan.get('description', '')}

src/main.py inhoud:
```python
{main_content[:3000]}
```

Genereer realistische test scenarios. Antwoord ALLEEN met dit JSON:
{{
  "scenarios": [
    {{
      "name": "korte beschrijving",
      "args": ["argument1", "argument2"],
      "expect_in_stdout": ["string1 die in output zou moeten staan"],
      "expect_no_error": true
    }}
  ]
}}

REGELS:
- args is een lijst van CLI argumenten zoals een gebruiker zou typen
- Voor web apps: gebruik args = ["--help"] (we testen alleen dat het start)
- Voor CLI tools: bedenk realistische input
- expect_in_stdout: keywords die in een correcte output zouden moeten staan (bv. cijfers, woorden, JSON-keys)
- Als project externe API's gebruikt: scenario mag "expect_no_error": false hebben (alleen check dat het niet crasht)
- 2-3 scenarios is genoeg

Geen uitleg, alleen het JSON object."""

        response = self.llm.generate(prompt, role="judge", temperature=0.3, stream=False)
        result = extract_json(response, expect="object")
        if not result or "scenarios" not in result:
            return []
        return result.get("scenarios", [])

    def _run_scenario(self, image_tag: str, scenario: dict, timeout: int = 30) -> dict:
        """Voer één scenario uit in de Docker container."""
        cmd = ["docker", "run", "--rm", image_tag, "python", "-m", "src.main"]
        cmd.extend(scenario.get("args", []))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "name": scenario.get("name", "unnamed"),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "args": scenario.get("args", [])
            }
        except subprocess.TimeoutExpired:
            return {
                "name": scenario.get("name", "unnamed"),
                "exit_code": -1,
                "stdout": "",
                "stderr": "TIMEOUT",
                "args": scenario.get("args", [])
            }
        except Exception as e:
            return {
                "name": scenario.get("name", "unnamed"),
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "args": scenario.get("args", [])
            }

    def _evaluate_scenario(self, scenario: dict, run_result: dict) -> dict:
        """Check of het run resultaat aan de verwachtingen voldoet."""
        passed = True
        reasons = []

        # Exit code check
        if scenario.get("expect_no_error", True) and run_result["exit_code"] != 0:
            passed = False
            reasons.append(f"exit code {run_result['exit_code']} (verwacht 0)")

        # Crash check (altijd, ongeacht expect_no_error)
        stderr_lower = run_result.get("stderr", "").lower()
        crash_keywords = ["traceback", "modulenotfounderror", "syntaxerror", "importerror", "indentationerror"]
        for kw in crash_keywords:
            if kw in stderr_lower:
                passed = False
                reasons.append(f"crash gedetecteerd: {kw}")
                break

        # Expected strings in stdout
        stdout = run_result.get("stdout", "")
        for expected in scenario.get("expect_in_stdout", []):
            if expected.lower() not in stdout.lower():
                passed = False
                reasons.append(f"missing in output: '{expected}'")

        return {
            "passed": passed,
            "reasons": reasons,
            "scenario_name": scenario.get("name", "unnamed")
        }

    def run(self, plan: dict, build_result: dict) -> dict:
        """Hoofdfunctie: genereer scenarios, draai ze, oordeel."""
        project_path = Path(build_result["project_path"])
        project_name = project_path.name
        image_tag = f"ai-factory/{project_name}:test"

        print(f"\n[functional] genereer test scenarios...")
        scenarios = self._generate_scenarios(plan, project_path)

        if not scenarios:
            print("[functional] geen scenarios gegenereerd, skip")
            return {"passed": True, "scenarios_run": 0, "results": []}

        print(f"[functional] {len(scenarios)} scenarios uitvoeren...")
        results = []
        all_passed = True

        for scenario in scenarios:
            print(f"[functional] - {scenario.get('name', 'unnamed')}")
            run_result = self._run_scenario(image_tag, scenario)
            evaluation = self._evaluate_scenario(scenario, run_result)
            results.append({
                "scenario": scenario,
                "run": run_result,
                "evaluation": evaluation
            })
            if not evaluation["passed"]:
                all_passed = False
                print(f"[functional]   FAIL: {evaluation['reasons']}")
            else:
                print(f"[functional]   OK")

        return {
            "passed": all_passed,
            "scenarios_run": len(scenarios),
            "results": results
        }
