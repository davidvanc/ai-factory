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
   - Het project gebruikt het standaard service_template (al aanwezig in src/service_template/)
   - src/main.py MOET er zo uitzien:

     from src.service_template.bootstrap import create_app
     from src.routes import router as business_router

     app = create_app(
         title="<beschrijvende naam>",
         version="0.1.0",
         business_routers=[business_router],
     )

   - Definieer je eigen endpoints in src/routes.py als APIRouter
   - GEEN @app.get/@app.post in main.py - alles in routes.py
   - Voor request bodies: gebruik Pydantic BaseModel klassen
   - Returns altijd JSON-serializable types
   - GEEN handmatige /health, /ready, /metrics endpoints maken - die komen automatisch van het template
   - Voor logging: from src.service_template.logging_config import get_logger; log = get_logger("naam")
   - Voor settings: from src.service_template.settings import settings (eigen settings extenden via subclass)

0b. SECURITY EN RESILIENCE (kritisch om te WETEN, niet om handmatig te bouwen):
   - Het service_template levert AUTOMATISCH:
     * Rate limiting (slowapi, opt-in via env var)
     * Bearer token auth (opt-in, voor business endpoints)
     * Security headers (X-Content-Type-Options, X-Frame-Options, HSTS)
     * Request timeout (30s default)
     * Request body size limit (1MB default)
     * CORS (configureerbaar)
   - Voor endpoints die auth NODIG hebben:
     from src.service_template.auth import verify_bearer_token
     from fastapi import Depends
     @router.post("/secure-endpoint")
     async def my_endpoint(token: str = Depends(verify_bearer_token), ...):
   - Voor extra rate limit per endpoint:
     from src.service_template.rate_limit import limiter
     @router.get("/expensive-endpoint")
     @limiter.limit("5/minute")
     async def my_endpoint(request: Request, ...):
   - GEEN custom auth, CORS of rate limiting code schrijven - gebruik het template

0c. TESTING DISCIPLINE (kritisch - 80% coverage gate):
   - Elke business module (logic.py, routes.py, etc.) MOET tests hebben
   - Coverage gate is 80% van src/ (uitgesloten: src/main.py en src/service_template/)
   - Test bestanden moeten een 'test_' prefix hebben en in tests/ staan
   - GEBRUIK de standaard fixtures uit tests/conftest.py:
     * 'client': TestClient voor HTTP integration tests
     * 'auth_headers': dict met Bearer token voor secure endpoints
   - Schrijf 3 soorten tests:
     1. Unit tests: test pure functies in logic.py zonder FastAPI
     2. Integration tests: test endpoints via 'client' fixture
     3. Edge cases: lege input, ongeldige format, grenswaarden
   - GEEN dummy tests die alleen "assert True" doen
   - Test ELKE error path: ongeldige input → 422, niet gevonden → 404, etc.
   - Voorbeeld goede test:
     def test_convert_returns_correct_rgb(client):
         r = client.post("/convert", json=dict(hex="#FF0000"))
         assert r.status_code == 200
         body = r.json()
         assert body["rgb"]["r"] == 255
     def test_convert_rejects_invalid_hex(client):
         r = client.post("/convert", json=dict(hex="ZZZ"))
         assert r.status_code == 422

0d. DATABASE GEBRUIK (alleen als needs_database=true in plan):
   - Database komt via SQLAlchemy 2.0 async API uit het service_template
   - Definieer je eigen models in src/models.py:
     from src.service_template.database import Base
     from sqlalchemy import Column, String, DateTime, Integer
     from datetime import datetime
     class Customer(Base):
         __tablename__ = "customers"
         id = Column(Integer, primary_key=True, autoincrement=True)
         name = Column(String(200), nullable=False)
         created_at = Column(DateTime, default=datetime.utcnow)
   - In endpoints: gebruik de get_db dependency:
     from fastapi import Depends
     from sqlalchemy.ext.asyncio import AsyncSession
     from src.service_template.database import get_db
     @router.post("/customers")
     async def create_customer(payload: CustomerIn, db: AsyncSession = Depends(get_db)):
         customer = Customer(name=payload.name)
         db.add(customer)
         await db.flush()
         return dict(id=customer.id, name=customer.name)
   - VOOR DE EERSTE RUN: Alembic migraties zijn al ingesteld - maak een initial migration:
     De Tester verwacht dat tabellen bestaan. Voeg in src/models.py een init_models() async functie toe
     die Base.metadata.create_all gebruikt voor TESTS. In productie gebruik je Alembic.
   - Voor TESTS: gebruik een aparte test-database of in-memory SQLite via TestClient fixtures

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
