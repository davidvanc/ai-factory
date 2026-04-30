import json
from src.llm.client import LLMClient

class DeveloperAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, plan: dict, feedback: dict = None) -> dict:
        feedback_section = ""
        if feedback:
            feedback_section = f"""

=== EERDERE POGING FAALDE - LEES DIT ZORGVULDIG ===
Je hebt deze code al eerder geschreven. Hij faalde om deze redenen:

{feedback.get('summary', 'Geen samenvatting')}

Specifieke problemen:
{json.dumps(feedback.get('issues', []), indent=2, ensure_ascii=False)}

Test output (laatste 1000 chars):
{feedback.get('test_output', 'Geen test output')[:1000]}

LOS DEZE PROBLEMEN OP IN JE NIEUWE VERSIE. Schrijf de complete code opnieuw, niet alleen patches.
"""

        prompt = f"""Je bent een expert Python developer. Schrijf alle code voor dit project:

Project: {plan['project_name']}
Beschrijving: {plan['description']}
Bestanden: {json.dumps(plan['structure'], indent=2)}
Requirements: {json.dumps(plan['requirements'], indent=2)}
Tests die moeten slagen: {json.dumps(plan['tests'], indent=2)}
Docker poort: {plan['docker_port']}
{feedback_section}
KRITISCHE REGELS - LEES ZORGVULDIG:

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

7. ENTRY POINT:
   - src/main.py is de hoofdfile
   - Voor CLI: gebruik argparse, exit cleanly bij missing args
   - Voor web: definieer 'app' (FastAPI) of vergelijkbaar

Antwoord in dit exacte JSON formaat - GEEN uitleg, alleen het JSON object:
{{
  "files": [
    {{"path": "src/main.py", "content": "volledige code hier"}},
    {{"path": "src/module.py", "content": "..."}},
    {{"path": "tests/test_module.py", "content": "..."}}
  ]
}}"""

        response = self.llm.generate(prompt, role="developer", temperature=0.2)

        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]

        return json.loads(json_str)
