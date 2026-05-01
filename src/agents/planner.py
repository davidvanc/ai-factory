import json
from src.llm.client import LLMClient
from src.llm.memory_client import MemoryClient
from src.agents.detector import DomainDetector
from src.agents.consultant_scientific import ScientificConsultant
from src.agents.consultant_scraper import ScraperConsultant


class PlannerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryClient()
        self.detector = DomainDetector()

    def _gather_consultants(self, task: str) -> str:
        """Detecteer domein en raadpleeg de juiste consultants."""
        detection = self.detector.detect(task)
        print(f"[planner] domein detectie: {detection['domains']} ({detection['confidence']}, {detection['method']})")

        consultant_context = ""

        if "scientific" in detection["domains"]:
            print(f"[planner] roep Scientific Consultant aan...")
            try:
                sc = ScientificConsultant()
                result = sc.consult(task)
                consultant_context += "\n\n" + sc.to_planner_context(result)
            except Exception as e:
                print(f"[planner] scientific consultant faalde: {e}")

        if "scraping" in detection["domains"]:
            print(f"[planner] roep Scraper Consultant aan...")
            try:
                sc = ScraperConsultant()
                result = sc.consult(task, max_pages=3)
                consultant_context += "\n\n" + sc.to_planner_context(result)
            except Exception as e:
                print(f"[planner] scraper consultant faalde: {e}")

        return consultant_context

    def run(self, task: str) -> dict:
        # Memory lessen ophalen
        lessons = self.memory.get_relevant_lessons(task, limit=10)

        lessons_section = ""
        if lessons:
            lessons_section = "\n\n=== LESSEN UIT VORIGE PROJECTEN ===\n"
            for l in lessons:
                lessons_section += f"- [{l.get('category')}] {l.get('pattern', '')[:150]}"
                if l.get('fix'):
                    lessons_section += f" → fix: {l['fix']}"
                lessons_section += f" (gezien {l.get('occurrence_count', 1)}x)\n"

        # Consultants raadplegen
        consultant_context = self._gather_consultants(task)

        prompt = f"""Je bent een software architect. Een gebruiker wil het volgende bouwen:

{task}
{consultant_context}
{lessons_section}

Maak een gedetailleerd projectplan in JSON formaat met deze exacte structuur:
{{
  "project_name": "korte_naam_zonder_spaties",
  "description": "wat het project doet",
  "structure": [
    "src/main.py",
    "src/module.py",
    "tests/test_main.py"
  ],
  "tests": [
    "test dat de hoofdfunctie werkt",
    "test dat de output correct is"
  ],
  "requirements": [
    "requests",
    "python-dotenv"
  ],
  "docker_port": 8080
}}

Als er WETENSCHAPPELIJKE CONTEXT of LIVE WEB DATA hierboven staat, GEBRUIK die expliciet bij het opstellen van structure, tests en requirements.

Antwoord ALLEEN met het JSON object, geen uitleg."""

        response = self.llm.generate(prompt, role="planner", temperature=0.3)

        from src.llm.json_utils import extract_json
        result = extract_json(response, expect="object")
        if result is None:
            raise ValueError(f"Planner: kon geen JSON extraheren uit response (lengte {len(response)})")
        return result
