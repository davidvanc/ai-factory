import json
from src.llm.client import LLMClient

class PlannerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, task: str) -> dict:
        prompt = f"""Je bent een software architect. Een gebruiker wil het volgende bouwen:

{task}

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

        # JSON extraheren uit response
        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]

        return json.loads(json_str)
