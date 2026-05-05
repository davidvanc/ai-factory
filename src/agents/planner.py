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

Maak een gedetailleerd projectplan voor een MICROSERVICE in JSON formaat.

ARCHITECTUUR REGELS (kritisch):
- Default: het project is een HTTP MICROSERVICE met FastAPI
- Endpoints zijn werkwoorden of resources, bv. POST /convert, GET /calculate, GET /status
- ALLE business logic is bereikbaar via HTTP endpoints, geen pure CLI tools
- src/main.py definieert de FastAPI 'app' variabele
- Alleen als de taak ECHT geen service kan zijn (bv. "schrijf een eenmalig migratie-script"), maak je een CLI

REGELS VOOR ENDPOINTS:
- Documenteer elk endpoint in 'endpoints' lijst met method + path + body/params + voorbeeld
- Voor input: gebruik query parameters (eenvoudige data) of JSON body (complexere data)
- Output: altijd JSON

DATABASE BESLISSING:
- needs_database=false is de DEFAULT voor onze factory
- Database-services worden HANDMATIG geschreven, NIET via factory
- Alleen als de gebruiker EXPLICIET vraagt om een database EN je 100% zeker bent: needs_database=true
- Bij elke andere taak: needs_database=false (zelfs als state normaal nodig zou zijn)
- We kunnen state simuleren met in-memory dicts voor demos

JSON STRUCTUUR:
{{
  "project_name": "korte_naam_zonder_spaties",
  "description": "wat de service doet",
  "is_service": true,
  "needs_database": false,
  "structure": [
    "src/main.py",
    "src/routes.py",
    "src/logic.py",
    "tests/test_routes.py"
  ],
  "endpoints": [
    {{
      "method": "POST",
      "path": "/convert",
      "description": "wat het doet",
      "request_example": {{"value": "FF5733"}},
      "response_example": {{"rgb": [255, 87, 51]}},
      "curl_example": "curl -X POST http://localhost:PORT/convert -H 'Content-Type: application/json' -d '{{\\"value\\": \\"FF5733\\"}}'"
    }}
  ],
  "tests": [
    "test dat POST /convert correct werkt voor geldige input",
    "test dat ongeldige input een 422 status geeft"
  ],
  "requirements": [
    "fastapi",
    "uvicorn",
    "pydantic"
  ]
}}

KRITISCH: Elke endpoint MOET hebben:
- request_example (dict met EXACT de velden die je in de Pydantic model gebruikt)
- response_example
- curl_example (gebruik PORT placeholder, geen hardcoded poort)

Antwoord ALLEEN met het JSON object, geen uitleg.

Als er WETENSCHAPPELIJKE CONTEXT of LIVE WEB DATA hierboven staat, GEBRUIK die expliciet bij het opstellen van structure, tests en requirements.

Antwoord ALLEEN met het JSON object, geen uitleg."""

        response = self.llm.generate(prompt, role="planner", temperature=0.3)

        from src.llm.json_utils import extract_json
        result = extract_json(response, expect="object")
        if result is None:
            raise ValueError(f"Planner: kon geen JSON extraheren uit response (lengte {len(response)})")
        return result
