import json
from pathlib import Path
from src.llm.client import LLMClient


class JudgeAgent:
    def __init__(self):
        self.llm = LLMClient()

    def _read_project_files(self, project_path: Path) -> str:
        """Lees alle relevante bestanden uit het project en bundel ze."""
        relevant_extensions = {".py", ".yml", ".yaml", ".txt", ".md", "Dockerfile"}
        parts = []
        for f in sorted(project_path.rglob("*")):
            if not f.is_file():
                continue
            if f.name.startswith("."):
                continue  # skip .env, .gitignore etc.
            if f.suffix in relevant_extensions or f.name == "Dockerfile":
                try:
                    content = f.read_text()
                    rel = f.relative_to(project_path)
                    parts.append(f"--- {rel} ---\n{content}")
                except Exception:
                    pass
        return "\n\n".join(parts)

    def run(self, plan: dict, build_result: dict, test_result: dict) -> dict:
        project_path = Path(build_result["project_path"])
        project_files = self._read_project_files(project_path)

        prompt = f"""Je bent een pragmatische senior code reviewer voor een autonoom AI software systeem.
Jouw taak: bepaal of dit project klaar is voor release.

=== ORIGINEEL PLAN ===
Project: {plan['project_name']}
Beschrijving: {plan['description']}
Geplande tests: {json.dumps(plan['tests'], indent=2)}

=== TEST RESULTATEN ===
Pytest geslaagd: {test_result.get('passed', False)}
Stappen uitgevoerd: {[s['name'] for s in test_result.get('steps', [])]}

=== PROJECT BESTANDEN ===
{project_files}

=== JOUW TAAK ===
Beoordeel of dit project een MINIMUM VIABLE PRODUCT is. Wees pragmatisch:
- APPROVED = doet wat het plan zegt, draait, geen kritieke bugs, basis-documentatie aanwezig
- REJECTED = code klopt niet met plan, kritieke bugs, ontbrekende essentiele bestanden, security issues

GEEN reden voor REJECTED:
- Ontbrekende linters/coverage tools
- Geen extra validatie boven wat plan beschrijft
- Stilistische voorkeuren
- Suggesties voor "robuustere" implementaties
- Code style preferences (single vs double quotes, etc.)

WEL reden voor REJECTED:
- Code doet niet wat plan beschrijft (functional mismatch)
- Tests falen of testen verkeerde dingen
- Hardcoded secrets/passwords/keys
- Crashes bij normale input
- Missing README/Dockerfile/requirements.txt
- Logische bugs (bv. test verwacht X, code levert geen X)
- TODO comments in productie code

Antwoord ALLEEN met een JSON object in dit exacte formaat:

{{
  "functional_match": {{
    "pass": true_of_false,
    "reason": "korte uitleg of de code doet wat het plan beschrijft"
  }},
  "security": {{
    "pass": true_of_false,
    "reason": "alleen REJECTED bij echte security issues (hardcoded keys, command injection, etc.)"
  }},
  "documentation": {{
    "pass": true_of_false,
    "reason": "is er een README waarmee een mens dit kan draaien? Basis is genoeg."
  }},
  "code_quality": {{
    "pass": true_of_false,
    "reason": "alleen REJECTED bij echte bugs of kritieke issues"
  }},
  "overall_verdict": "APPROVED" of "REJECTED",
  "verdict_reason": "samenvattende motivatie (max 2 zinnen)",
  "improvements": [
    "nice-to-have suggestie 1",
    "nice-to-have suggestie 2"
  ]
}}

improvements zijn optionele verbeterideeen, NIET de reden voor rejection.
Een project mag APPROVED zijn met openstaande improvements - die zijn voor een volgende iteratie."""

        response = self.llm.generate(prompt, role="judge", temperature=0.2)

        # JSON extraheren uit response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end <= start:
            return {
                "overall_verdict": "REJECTED",
                "verdict_reason": "Judge gaf geen valide JSON terug",
                "raw_response": response[:500]
            }

        try:
            return json.loads(response[start:end])
        except json.JSONDecodeError as e:
            return {
                "overall_verdict": "REJECTED",
                "verdict_reason": f"JSON parse error: {e}",
                "raw_response": response[:500]
            }
