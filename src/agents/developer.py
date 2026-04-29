import json
from src.llm.client import LLMClient

class DeveloperAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, plan: dict) -> dict:
        prompt = f"""Je bent een expert Python developer. Schrijf alle code voor dit project:

Project: {plan['project_name']}
Beschrijving: {plan['description']}
Bestanden: {json.dumps(plan['structure'], indent=2)}
Requirements: {json.dumps(plan['requirements'], indent=2)}
Tests die moeten slagen: {json.dumps(plan['tests'], indent=2)}
Docker poort: {plan['docker_port']}

Schrijf ALLE bestanden volledig uit. Antwoord in dit exacte JSON formaat:
{{
  "files": [
    {{
      "path": "src/main.py",
      "content": "volledige inhoud van het bestand"
    }},
    {{
      "path": "tests/test_main.py",
      "content": "volledige test code"
    }}
  ]
}}

Regels:
- Geen secrets of API keys in de code
- Gebruik environment variables via os.getenv()
- Alle tests moeten kunnen slagen
- Antwoord ALLEEN met het JSON object, geen uitleg"""

        response = self.llm.generate(prompt, role="developer", temperature=0.2)

        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]

        return json.loads(json_str)

