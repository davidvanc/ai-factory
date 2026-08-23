"""
Developer-agent: schrijft de code voor een gepland project.

Genereert **per bestand** in plaats van het hele project als een JSON-blob.
Waarom: die blob liep tegen de max_tokens-grens aan zodra een project iets
groter werd. Reasoning-modellen verstoken daar het leeuwendeel van (gemeten:
78% bij Gemini 3.1 Pro), waarna het antwoord midden in de JSON afbrak en alles
verloren was terwijl je de volle prijs betaalde. Per bestand is elk antwoord
klein genoeg om nooit af te kappen, mislukt er een dan raak je alleen dat ene
bestand kwijt, en bij een retry herschrijf je enkel de bestanden die de fout
veroorzaakten in plaats van het hele project.

Consistentie tussen bestanden komt van de volgorde: de contracten (models,
config, errors) worden eerst geschreven en gaan daarna letterlijk mee als
context, zodat latere bestanden niet kunnen fantaseren over wat er bestaat.

De vaste instructies staan vooraan in de prompt en zijn bij elke aanroep
byte-identiek, zodat prompt caching ze na het eerste bestand bijna gratis maakt.
"""
import json
from typing import Optional, Dict, Any, List

from src.llm.client import LLMClient
from src.llm.json_utils import extract_json

# Bestanden die contracten vastleggen waar de rest zich aan moet houden.
# Die gaan eerst, zodat latere bestanden ze letterlijk in hun context krijgen.
CONTRACT_BESTANDEN = (
    "constants.py", "types.py", "errors.py", "config.py", "models.py", "schemas.py",
)

# Foutmeldingen die zeggen "de afspraak zelf klopt niet", niet "deze regel is fout".
# Bij een van deze gaan de contractbestanden mee in de herschrijfset, ook als hun
# naam nergens in de traceback staat - anders repareert de pipeline om de
# oorzaak heen en blijft die staan.
CONTRACT_SIGNALEN = (
    "importerror", "modulenotfounderror", "attributeerror", "nameerror",
    "has no attribute", "unexpected keyword argument", "cannot import name",
    "validation error", "field required", "is not defined",
)


class DeveloperAgent:
    def __init__(self):
        self.llm = LLMClient()

    # =========================
    # PUBLIEKE API (ongewijzigd contract met de pipeline)
    # =========================

    def run(
        self,
        plan: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None,
        role_override: str = "developer",
    ) -> Dict[str, Any]:
        paden = self._bestandsvolgorde(plan)
        if not paden:
            raise ValueError("Developer: het plan bevat geen 'structure' met bestandspaden")

        vorige = {
            f["path"]: f.get("content", "")
            for f in (feedback or {}).get("previous_files", [])
            if f.get("path")
        }
        opnieuw = self._te_herschrijven(paden, vorige, feedback)

        vaste_kop = self._vaste_kop(plan, feedback)
        geschreven: List[Dict[str, str]] = []

        hergebruikt = [p for p in paden if p not in opnieuw and p in vorige]
        if hergebruikt:
            print(
                f"[developer] {len(hergebruikt)} bestand(en) ongewijzigd overgenomen, "
                f"{len(opnieuw)} opnieuw te schrijven",
                flush=True,
            )

        gecontroleerd = False
        nieuw_contract = False

        for i, pad in enumerate(paden, 1):
            if pad not in opnieuw and pad in vorige:
                geschreven.append({"path": pad, "content": vorige[pad]})
                continue

            # Zodra de contracten staan en er iets op gebouwd gaat worden:
            # eerst controleren. Daarna is corrigeren veel duurder, want dan
            # heeft alles zich er al naar gevormd.
            if not gecontroleerd and self._is_bouwbestand(pad) and nieuw_contract:
                geschreven = self._controleer_contracten(plan, geschreven, role_override)
                gecontroleerd = True

            print(f"[developer] bestand {i}/{len(paden)}: {pad}", flush=True)
            staart = self._staart(pad, geschreven, vorige.get(pad))
            inhoud = self.llm.generate(
                vaste_kop + staart,
                role=role_override,
                temperature=0.2,
                cache_prefix_len=len(vaste_kop),
            )
            inhoud = self._strip_fences(inhoud)
            if not inhoud.strip() and not pad.endswith("__init__.py"):
                raise ValueError(f"Developer: leeg antwoord voor {pad}")
            geschreven.append({"path": pad, "content": inhoud})
            if self._is_contract(pad):
                nieuw_contract = True

        return {"files": geschreven}

    # =========================
    # CONTRACTCONTROLE
    # =========================

    @staticmethod
    def _is_contract(pad: str) -> bool:
        return pad.split("/")[-1] in CONTRACT_BESTANDEN

    @staticmethod
    def _is_bouwbestand(pad: str) -> bool:
        """Alles wat op de contracten voortbouwt: logica, routes, main, tests."""
        naam = pad.split("/")[-1]
        return naam != "__init__.py" and naam not in CONTRACT_BESTANDEN

    def _controleer_contracten(
        self,
        plan: Dict[str, Any],
        geschreven: List[Dict[str, str]],
        role_override: str,
    ) -> List[Dict[str, str]]:
        """Houdt de contractbestanden tegen het plan voor de rest erop gebouwd wordt.

        Een fout contract is het duurste soort fout in deze opzet: elk volgend
        bestand krijgt het letterlijk mee en plooit zich ernaar, tests incluis.
        Zo'n project komt door de tester heen en is toch verkeerd. Deze controle
        kost een kleine aanroep over kleine bestanden.
        """
        contracten = [f for f in geschreven if self._is_contract(f["path"])]
        if not contracten:
            return geschreven

        code = "\n\n".join(f"--- {f['path']} ---\n{f['content']}" for f in contracten)
        prompt = f"""Je controleert de datacontracten van een service voordat de rest erop gebouwd wordt.

Dit is het plan:
Beschrijving: {plan['description']}
Endpoints: {json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}
Tests die straks moeten slagen: {json.dumps(plan['tests'], indent=2, ensure_ascii=False)}

Dit zijn de geschreven contractbestanden:
{code}

Controleer ALLEEN deze punten:
1. Kan elk endpoint uit het plan zijn request en response opbouwen met deze modellen?
2. Ontbreken er velden die de geplande tests nodig hebben?
3. Kloppen de types en de verplicht/optioneel-keuzes met wat het plan beschrijft?
4. Zijn er velden of klassen die nergens voor dienen?

Beoordeel NIET de stijl, de naamgeving of de implementatie. Alleen of de
contracten kloppen met het plan.

Antwoord met alleen JSON:
{{"ok": true}}
of
{{"ok": false, "problemen": ["concreet probleem 1", "concreet probleem 2"]}}"""

        print("[developer] contractcontrole...", flush=True)
        try:
            antwoord = self.llm.generate(prompt, role="contract_review", temperature=0.0)
            oordeel = extract_json(antwoord, expect="object")
        except Exception as e:
            # De controle mag de pipeline nooit tegenhouden.
            print(f"[developer] contractcontrole overgeslagen: {e}", flush=True)
            return geschreven

        if not oordeel or oordeel.get("ok") is not False:
            print("[developer] contractcontrole: ok", flush=True)
            return geschreven

        problemen = oordeel.get("problemen") or []
        print(f"[developer] contractcontrole: {len(problemen)} probleem(en), "
              f"contracten worden herschreven", flush=True)
        for pr in problemen:
            print(f"           - {pr}", flush=True)

        # Eenmalig herstellen. Blijft het fout, dan vangt de tester het verderop
        # op; nog een ronde hier maakt het vooral duurder.
        hersteld = []
        for f in geschreven:
            if not self._is_contract(f["path"]):
                hersteld.append(f)
                continue
            herstel_prompt = f"""{prompt}

=== GEVONDEN PROBLEMEN ===
{json.dumps(problemen, indent=2, ensure_ascii=False)}

Herschrijf nu {f['path']} zodat deze problemen opgelost zijn. Wijzig niets anders.
Antwoord met ALLEEN de volledige inhoud van {f['path']}, geen uitleg, geen fences."""
            try:
                nieuwe = self._strip_fences(
                    self.llm.generate(herstel_prompt, role=role_override, temperature=0.2)
                )
                hersteld.append({"path": f["path"], "content": nieuwe or f["content"]})
            except Exception as e:
                print(f"[developer] herstel van {f['path']} mislukt ({e}), "
                      f"oorspronkelijke versie blijft staan", flush=True)
                hersteld.append(f)
        return hersteld

    # =========================
    # WELKE BESTANDEN, IN WELKE VOLGORDE
    # =========================

    def _bestandsvolgorde(self, plan: Dict[str, Any]) -> List[str]:
        """Contracten eerst, dan logica, dan routes/main, dan tests."""
        paden = [p for p in (plan.get("structure") or []) if isinstance(p, str) and p.strip()]

        def sleutel(pad: str):
            naam = pad.split("/")[-1]
            is_test = "/tests/" in pad or pad.startswith("tests/") or naam.startswith("test_")
            if naam == "__init__.py":
                return (0, 0, pad)
            if naam in CONTRACT_BESTANDEN:
                return (1, CONTRACT_BESTANDEN.index(naam), pad)
            if naam == "conftest.py":
                return (5, 0, pad)
            if is_test:
                return (6, 0, pad)
            if naam == "main.py":
                return (4, 0, pad)
            if naam == "routes.py":
                return (3, 0, pad)
            return (2, 0, pad)

        return sorted(paden, key=sleutel)

    def _te_herschrijven(
        self,
        paden: List[str],
        vorige: Dict[str, str],
        feedback: Optional[Dict[str, Any]],
    ) -> set:
        """Bij een eerste poging alles; bij een retry alleen wat de fout raakt."""
        if not feedback or not vorige:
            return set(paden)

        genoemd = feedback.get("implicated_paths")
        if genoemd:
            opnieuw = {p for p in paden if p in set(genoemd)}
        else:
            # Vangnet als de pipeline geen lijst meegeeft: zoek bestandsnamen in de tekst.
            tekst = " ".join([
                str(feedback.get("summary", "")),
                json.dumps(feedback.get("issues", []), ensure_ascii=False),
                str(feedback.get("test_output", "") or ""),
            ]).lower()
            opnieuw = {
                p for p in paden
                if p.split("/")[-1].lower() in tekst or p.lower() in tekst
            }

        # Bestanden die nog niet bestaan moeten sowieso geschreven worden.
        opnieuw |= {p for p in paden if p not in vorige}

        tekst = " ".join([
            str(feedback.get("summary", "")),
            json.dumps(feedback.get("issues", []), ensure_ascii=False),
            str(feedback.get("test_output", "") or ""),
        ]).lower()

        # Ruikt het naar een contractprobleem, dan zijn de contracten verdacht -
        # ook als hun naam nergens in de traceback staat. Zonder dit repareert
        # de pipeline om de oorzaak heen en blijft die staan.
        if any(sig in tekst for sig in CONTRACT_SIGNALEN):
            contracten = {p for p in paden if self._is_contract(p)}
            if contracten - opnieuw:
                print("[developer] contractsignaal in de testoutput: "
                      "contractbestanden gaan mee in de herschrijfset", flush=True)
            opnieuw |= contracten

        # Twee of meer eerdere failures in deze run: gericht repareren is gokwerk
        # geworden. Alles opnieuw, contracten incluis.
        if len(feedback.get("history") or []) >= 2:
            print("[developer] derde poging zonder doorbraak: alles opnieuw schrijven",
                  flush=True)
            return set(paden)

        # Niets herkend? Dan is gericht repareren gokwerk - schrijf alles opnieuw.
        return opnieuw or set(paden)

    # =========================
    # PROMPT
    # =========================

    def _vaste_kop(self, plan: Dict[str, Any], feedback: Optional[Dict[str, Any]]) -> str:
        """Het deel dat bij elk bestand identiek is, zodat caching het bijna gratis maakt."""
        feedback_section = self._build_feedback_section(feedback) if feedback else ""
        return (
            "Je bent een expert Python developer. Je schrijft de code voor dit project,\n"
            "bestand per bestand. Per aanroep lever je exact een bestand.\n\n"
            f"Project: {plan['project_name']}\n"
            f"Beschrijving: {plan['description']}\n"
            f"Bestanden in dit project: {json.dumps(plan['structure'], indent=2)}\n"
            f"Requirements: {json.dumps(plan['requirements'], indent=2)}\n"
            f"Tests die moeten slagen: {json.dumps(plan['tests'], indent=2, ensure_ascii=False)}\n"
            f"Endpoints om te implementeren: "
            f"{json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}\n"
            f"{feedback_section}\n"
            f"{REGELS}"
        )

    def _staart(
        self,
        pad: str,
        geschreven: List[Dict[str, str]],
        vorige_versie: Optional[str],
    ) -> str:
        """Het wisselende deel: context van al geschreven bestanden plus de opdracht."""
        delen = []

        if geschreven:
            delen.append("\n=== AL GESCHREVEN BESTANDEN IN DIT PROJECT ===\n")
            delen.append(
                "Blijf hier exact mee consistent: importeer wat hier bestaat, verzin geen\n"
                "functies, klassen of velden die er niet in staan. Herhaal ze NIET.\n\n"
            )
            for f in geschreven:
                delen.append(f"--- {f['path']} ---\n{f['content']}\n\n")

        if vorige_versie:
            delen.append(f"\n=== JE VORIGE VERSIE VAN {pad} ===\n")
            delen.append(
                "Neem dit als basis en pas alleen aan wat nodig is om de gerapporteerde\n"
                "problemen op te lossen.\n\n"
            )
            delen.append(vorige_versie + "\n\n")

        delen.append(
            "\n=== JOUW OPDRACHT ===\n"
            f"Schrijf nu exact een bestand: {pad}\n\n"
            f"Antwoord met ALLEEN de volledige inhoud van {pad}. Geen uitleg vooraf of\n"
            "achteraf, geen markdown code fences, geen bestandsnaam als kop, geen JSON.\n"
            "Begin direct met de eerste regel van het bestand.\n"
        )
        return "".join(delen)

    # =========================
    # ANTWOORD OPSCHONEN
    # =========================

    @staticmethod
    def _strip_fences(tekst: str) -> str:
        """Haalt een markdown-fence weg die het hele antwoord omsluit.

        Alleen als het antwoord als geheel omwikkeld is - een README mag zelf
        gewoon code fences bevatten en die moeten blijven staan.
        """
        regels = tekst.strip().split("\n")
        while regels and not regels[0].strip():
            regels.pop(0)
        while regels and not regels[-1].strip():
            regels.pop()
        if (
            len(regels) >= 2
            and regels[0].lstrip().startswith("```")
            and regels[-1].strip() == "```"
        ):
            regels = regels[1:-1]
        return "\n".join(regels).rstrip() + "\n"

    # =========================
    # FEEDBACK BUILDING
    # =========================

    def _build_feedback_section(self, feedback: Dict[str, Any]) -> str:
        history_block = self._format_history(feedback.get("history"))
        preservation_block = self._build_preservation_block(feedback)

        summary = feedback.get("summary", "Geen samenvatting")
        issues = json.dumps(feedback.get("issues", []), indent=2, ensure_ascii=False)
        test_output = (feedback.get("test_output") or "")[:3000]

        return (
            f"\n{history_block}\n{preservation_block}\n\n"
            "=== GERAPPORTEERDE PROBLEMEN ===\n"
            f"Samenvatting: {summary}\n\n"
            f"Specifieke issues:\n{issues}\n\n"
            f"Test output (laatste 3000 chars):\n{test_output}\n"
        )

    def _format_history(self, history: Optional[List[str]]) -> str:
        if not history:
            return ""
        history_lines = "\n".join(history)
        return (
            "\nGESCHIEDENIS VAN ALLE EERDERE FAILURES IN DEZE RUN:\n\n"
            f"{history_lines}\n\n"
            "KRITISCH: je moet ALLE bovenstaande issues TEGELIJKERTIJD oplossen.\n"
            "   - Een nieuwe tester-fail na een judge-rejection betekent meestal dat je een\n"
            "     hack hebt weggehaald zonder de echte bug te fixen.\n"
            "   - Een nieuwe judge-rejection na een tester-pass betekent meestal dat je een\n"
            "     hack hebt geintroduceerd om de tester te laten slagen.\n"
            "Doel: code die ZOWEL alle tests laat slagen ALS de Judge laat APPROVEN, zonder\n"
            "hardcoded shortcuts. Als je beide niet tegelijk kunt: kies eerlijke tester-fails\n"
            "boven hacks.\n"
        )

    def _build_preservation_block(self, feedback: Dict[str, Any]) -> str:
        summary = feedback.get("summary", "") or ""
        is_judge_rejection = "Tests failed" not in summary

        block = (
            "\nRETRY MODE - LEES DIT EERST EN ZORGVULDIG\n\n"
            "Dit is GEEN nieuwe taak. Je hebt eerder al een (deels) werkende versie\n"
            "geschreven. Je taak NU is NIET die versie opnieuw schrijven, maar ALLEEN de\n"
            "specifieke gerapporteerde problemen oplossen.\n\n"
            "ABSOLUTE REGELS (overtreden = falen):\n"
            "1. Wijzig alleen de specifieke regels of functies die nodig zijn om de\n"
            "   gerapporteerde failures op te lossen. Laat al het andere ongemoeid.\n"
            "2. Tests die eerder slaagden, MOETEN nu ook slagen. Als jouw nieuwe versie ook\n"
            "   maar een enkele eerder-slagende test breekt, heb je gefaald - ongeacht of de\n"
            "   gemelde issues opgelost zijn.\n"
            "3. Voeg GEEN nieuwe features, endpoints of tests toe die niet in het plan staan.\n"
            "4. Bij twijfel fix versus herschrijf: kies altijd fixen.\n"
        )
        if is_judge_rejection:
            block += (
                "\nEXTRA: in je vorige poging slaagden ALLE tests. De Judge heeft alleen\n"
                "kwaliteits-issues gemarkeerd. Los die op ZONDER ook maar een test te breken.\n"
                "Test-compatibiliteit is hard requirement, niet optioneel.\n"
            )
        return block


# De vaste huisregels. Bewust een gewone string en geen f-string: hier staat
# voorbeeldcode met accolades in, die anders geescaped zou moeten worden.
REGELS = """
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
   - Test ELKE error path: ongeldige input -> 422, niet gevonden -> 404, etc.
   - Voorbeeld goede test:
     def test_convert_returns_correct_rgb(client):
         r = client.post("/convert", json=dict(hex="#FF0000"))
         assert r.status_code == 200
         body = r.json()
         assert body["rgb"]["r"] == 255
     def test_convert_rejects_invalid_hex(client):
         r = client.post("/convert", json=dict(hex="ZZZ"))
         assert r.status_code == 422

0d. TEST ISOLATION (kritisch - voorkomt flaky tests in CI):
   - Heeft je service module-level state (counters, dicts, lists in storage.py of vergelijkbaar)?
     Dan MOET je de reset-fixture op TWEE plaatsen zetten. Empirisch is gebleken dat in deze
     build/test-omgeving de conftest.py autouse fixture niet altijd betrouwbaar firet -
     dezelfde fixture in het test-bestand zelf firet wel. Belt-and-suspenders is de stabiele oplossing.
   - Stappen die je verplicht moet zetten:
     1. Exporteer een reset functie uit de module met state:
        # src/database.py (of src/storage.py)
        _items: dict = {}
        _counter: int = 0

        def reset_state() -> None:
            global _counter
            _items.clear()
            _counter = 0
     2. Voeg de autouse fixture toe in tests/conftest.py:
        # tests/conftest.py
        import pytest
        from src.database import reset_state

        @pytest.fixture(autouse=True)
        def _reset_state_between_tests():
            reset_state()
            yield
     3. EN voeg dezelfde fixture ook toe bovenaan elk test-bestand
        (test_routes.py, test_logic.py, etc.) als backstop:
        # tests/test_routes.py (voor de eerste test)
        import pytest
        from src.database import reset_state

        @pytest.fixture(autouse=True)
        def _reset_state_between_tests():
            reset_state()
            yield
   - reset_state() zelf: gebruik dict.clear() voor in-place mutatie
     (NIET _dict = {} rebind), en `global ...` voor counters.
   - Stateloze services (pure computatie) hebben deze regel niet nodig.

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
   - Als een argument --no-foo heet in de plan-beschrijving, gebruik EXACT die naam
   - Geen short flags (-x) als alternatief tenzij expliciet gevraagd
   - Argument-namen moeten matchen met wat een gebruiker zou verwachten

7. EXTERNE DATA - LEES DIT ZORGVULDIG:
   - Als de taak data vereist van een specifieke website, gebruik HTML scraping (requests + BeautifulSoup)
   - Vermijd API's die een API key vereisen (tenzij expliciet vermeld in de plan/context)
   - Als het plan een specifieke API noemt zoals "Open-Meteo" - gebruik die
   - Voor overheidssites of wetenschappelijke bronnen: scrape de HTML met BeautifulSoup
   - Voor coordinaat-lookup: gebruik geopy met Nominatim (gratis, geen key)

8. ENTRY POINT:
   - src/main.py is de hoofdfile
   - Voor CLI: gebruik argparse, exit cleanly bij missing args
   - Voor web: definieer 'app' (FastAPI) of vergelijkbaar
"""
