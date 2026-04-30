import json
from src.llm.client import LLMClient
from src.llm.memory_client import MemoryClient


class PlannerAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryClient()

    def run(self, task: str) -> dict:
        # Geleerde lessen ophalen uit memory
        lessons = self.memory.get_relevant_lessons(task, limit=10)

        lessons_section = ""
        if lessons:
            lessons_section = "\n\n=== LESSEN UIT VORIGE PROJECTEN ===\n"
            lessons_section += "Deze patterns zijn eerder fout gegaan. Houd er rekening mee bij het plan:\n"
            for l in lessons:
                lessons_section += f"- [{l.get('category')}] {l.get('pattern', '')[:150]}"
                if l.get('fix'):
                    lessons_section += f" → fix: {l['fix']}"
                lessons_section += f" (gezien {l.get('occurrence_count', 1)}x)\n"

        prompt = f"""Je bent een software architect. Een gebruiker wil het volgende bouwen:

{task}
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

Antwoord ALLEEN met het JSON object, geen uitleg."""

        response = self.llm.generate(prompt, role="planner", temperature=0.3)

        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]

        return json.loads(json_str)
