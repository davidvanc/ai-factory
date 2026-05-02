import json
from src.llm.client import LLMClient

class DeveloperAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, plan: dict, feedback: dict = None, role_override: str = "developer") -> dict:
        feedback_section = ""
        if feedback:
            feedback_section = ""
        if feedback:
            previous_code = ""
            if feedback.get("previous_files"):
                previous_code = "\n\n=== JOUW VORIGE CODE (de basis voor je nieuwe versie) ===\n"
                for f in feedback["previous_files"]:
                    previous_code += f"\n--- {f['path']} ---\n{f['content']}\n"

            feedback_section = f"""

=== EERDERE POGING FAALDE ===
Je hebt deze code al eerder geschreven. Hij faalde om deze redenen:

{feedback.get('summary', 'Geen samenvatting')}

Specifieke problemen:
{json.dumps(feedback.get('issues', []), indent=2, ensure_ascii=False)}

Test output (laatste 3000 chars):
{feedback.get('test_output', 'Geen test output')[:3000]}
{previous_code}

KRITISCH: Behoud zoveel mogelijk van je vorige code. Pas ALLEEN aan wat nodig is om de fouten op te lossen.
- Schrijf NIET alles opnieuw vanaf nul
- Schrijf NIET nieuwe tests of features die niet in het plan staan
- Fix specifiek de gerapporteerde problemen
- Behoud bestaande logica die WEL werkte
"""

        prompt = f"""Je bent een expert Python developer. Schrijf alle code voor dit project:

Project: {plan['project_name']}
Beschrijving: {plan['description']}
Bestanden: {json.dumps(plan['structure'], indent=2)}
Requirements: {json.dumps(plan['requirements'], indent=2)}
Tests die moeten slagen: {json.dumps(plan['tests'], indent=2)}
Endpoints om te implementeren: {json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}
{feedback_section}
KRITISCHE REGELS - LEES ZORGVULDIG:

0. MICROSERVICE ARCHITECTUUR (kritisch):
   - Het project is een FastAPI service, GEEN CLI tool
   - src/main.py definieert: app = FastAPI()
   - Implementeer ELK endpoint uit het plan exact zoals beschreven
   - Endpoints uit plan moeten EXACT dezelfde method + path hebben als beschreven
   - Voor request bodies: gebruik Pydantic BaseModel klassen
   - Returns altijd JSON-serializable types (dict, list, primitives)
   - Voeg ALTIJD GET /health endpoint toe dat {{"status": "ok"}} teruggeeft

1. MAPPENSTRUCTUUR (vast, niet onderhandelbaar):
   - Source code in src/
   - Tests in tests/
   - Werkdirectory in container = /app
   - PYTHONPATH = /app

2. IMPORT REGELS (heel belangrijk):
   - In src/main.py importeer je andere src bestanden als: from src.module import X
   - In tests/test_X.py importeer je src bestanden als: from src.module import X
   - GEBRUIK NOOIT: from module (zonder src. prefix)
   - GEBRUIK NOOIT: sys.path.insert() of os.path tricks in tests

3. TESTS:
   - Gebruik pytest stijl (geen unittest.TestCase nodig)
   - Plain test_xxx() functies met assert statements
   - Imports altijd "from src.X import Y"

4. SECURITY:
   - Geen hardcoded secrets/keys
   - Gebruik os.getenv() voor configuratie

5. CODE COMPLEETHEID:
   - GEEN TODO comments, GEEN placeholders
   - Elke functie moet volledig werkend zijn
   - Als een test verwacht dat code X doet, MOET de code X doen
   - Geen comments zoals "voor simpliciteit doe ik X niet" als de tests Y verwachten

6. CLI ARGUMENTEN:
   - Als een argument `--no-foo` heet in de plan-beschrijving, gebruik EXACT die naam
   - Geen short flags (-x) als alternatief tenzij expliciet gevraagd
   - Argument-namen moeten matchen met wat een gebruiker zou verwachten

7. EXTERNE DATA - LEZ DIT ZORGVULDIG:
   - Als de taak data vereist van een specifieke website, gebruik HTML scraping (requests + BeautifulSoup)
   - Vermijd API's die een API key vereisen (tenzij expliciet vermeld in de plan/context)
   - Als het plan een specifieke API noemt zoals "Open-Meteo" - gebruik die
   - Voor overheidssites of wetenschappelijke bronnen: scrape de HTML met BeautifulSoup
   - Voorbeeld goed: kmi.be HTML parsen met BeautifulSoup voor weergegevens
   - Voorbeeld fout: aqicn.org API gebruiken (vereist key)
   - Voor coordinaat-lookup: gebruik geopy met Nominatim (gratis, geen key)

8. ENTRY POINT:
   - src/main.py is de hoofdfile
   - Voor CLI: gebruik argparse, exit cleanly bij missing args
   - Voor web: definieer 'app' (FastAPI) of vergelijkbaar

KRITISCH: Je antwoord moet ENKEL geldig JSON zijn. Geen uitleg vooraf, geen samenvatting achteraf, geen markdown code fences. Direct beginnen met {{ en eindigen met }}.

Antwoord ALLEEN met dit JSON formaat - GEEN andere tekst:
{{
  "files": [
    {{"path": "src/main.py", "content": "volledige code hier"}},
    {{"path": "src/module.py", "content": "..."}},
    {{"path": "tests/test_module.py", "content": "..."}}
  ]
}}"""

        response = self.llm.generate(prompt, role=role_override, temperature=0.2)

        from src.llm.json_utils import extract_json
        result = extract_json(response, expect="object")
        if result is None:
            raise ValueError(f"Developer: kon geen JSON extraheren uit response (lengte {len(response)}). Eerste 200 chars: {response[:200]}")
        return result
