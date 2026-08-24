"""
Designer-agent: denkt het hele project een keer door en legt per bestand vast
wat erin moet.

Waarom deze stap bestaat. De developer schreef eerst per bestand met een sterk
model. Elk bestand kreeg de volledige opdracht mee en begon opnieuw over het
hele probleem na te denken - gemeten op een base64-service: 19 aanroepen, 89%
van alle output-tokens ging naar redeneren, 35.606 tokens voor een bestand van
3.256 tekens. Het denkwerk gebeurde negentien keer.

Nu gebeurt het een keer. Deze agent levert per bestand een specificatie die
concreet genoeg is om zonder nadenken uit te schrijven: welke functies, welke
signatures, welk gedrag, welke fouten, welke imports. Het uitschrijven gaat
daarna naar een goedkoop model dat niet redeneert.

Bij een retry wordt hier opnieuw nagedacht, niet bij de schrijver: een
niet-redenerend model kan een bug niet bedenken.
"""
import json
from typing import Any, Dict, List, Optional

import requests

from src.llm.client import LLMClient, AntwoordAfgekapt
from src.llm.json_utils import extract_json


# Bestanden die contracten vastleggen. Die gaan in de eerste golf, zodat de
# rest hun definitieve specs al binnen heeft.
CONTRACT_NAMEN = (
    "constants.py", "types.py", "errors.py", "config.py", "models.py", "schemas.py",
)

# Bovengrens per ontwerpgolf. Gemeten ~3.300 output-tokens per bestand, dus acht
# blijft ruim onder de 64.000 en ver onder de timeout van 15 minuten.
MAX_PER_GOLF = 8

# Redenen om alsnog op te knippen: het antwoord paste niet, duurde te lang, of
# kwam er onbruikbaar uit. Alle drie betekenen "te veel in een keer gevraagd".
TE_VEEL_GEVRAAGD = (
    AntwoordAfgekapt,
    TimeoutError,
    requests.exceptions.Timeout,
)

# Eenmaal teruggevallen binnen een run, blijft het zo: een retry hoeft die dure
# les niet opnieuw te leren. Per proces, en een proces is een project.
_GOLVEN_NODIG = False


class DesignerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(
        self,
        plan: Dict[str, Any],
        paden: List[str],
        feedback: Optional[Dict[str, Any]] = None,
        role: str = "designer",
    ) -> Dict[str, str]:
        """Geeft {pad: specificatie} terug voor de gevraagde paden."""
        global _GOLVEN_NODIG

        if not _GOLVEN_NODIG and len(paden) > 1:
            # Eerst gewoon proberen. Dat is de goedkope weg en hij lukt voor
            # verreweg de meeste projecten.
            try:
                specs = self._ontwerp(plan, paden, {}, feedback, role)
                ontbreekt = [p for p in paden if p not in specs]
                if not ontbreekt:
                    return specs
                print(f"[designer] geen spec voor {ontbreekt} in een ronde - "
                      f"opnieuw in golven", flush=True)
            except TE_VEEL_GEVRAAGD as e:
                print(f"[designer] een ontwerpronde lukte niet ({type(e).__name__}), "
                      f"opnieuw in golven", flush=True)
            except ValueError as e:
                # Onparseerbare JSON is meestal ook 'te veel gevraagd'.
                print(f"[designer] antwoord onbruikbaar ({e}), opnieuw in golven",
                      flush=True)
            _GOLVEN_NODIG = True

        specs: Dict[str, str] = {}
        golven = self._golven(paden)
        for i, golf in enumerate(golven, 1):
            print(f"[designer] golf {i}/{len(golven)}: {len(golf)} bestand(en) "
                  f"({', '.join(golf)})", flush=True)
            specs.update(self._ontwerp(plan, golf, specs, feedback, role))

        ontbreekt = [p for p in paden if p not in specs]
        if ontbreekt:
            print(f"[designer] geen spec gekregen voor {ontbreekt} - "
                  f"die bestanden krijgen alleen het plan mee", flush=True)

        return self._controleer_specs(plan, specs, role)

    # =========================
    # ONTWERPCONTROLE
    # =========================

    def _controleer_specs(
        self,
        plan: Dict[str, Any],
        specs: Dict[str, str],
        role: str,
    ) -> Dict[str, str]:
        """Kijkt het hele ontwerp na voor er ook maar een regel geschreven wordt.

        Drie vragen, en niets anders. Een reviewer die ook over stijl en
        architectuur mag oordelen wordt een tweede ontwerper die met de eerste
        gaat ruzien, en dan verlies je goede specs.
        """
        if not specs:
            return specs

        alles = "\n\n".join(f"--- {pad} ---\n{spec}" for pad, spec in specs.items())
        prompt = f"""Je controleert het ontwerp van een service voordat de code geschreven wordt.

Dit is het plan:
Beschrijving: {plan.get('description', '')}
Endpoints: {json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}
Tests die moeten slagen: {json.dumps(plan.get('tests', []), indent=2, ensure_ascii=False)}

Dit is het ontwerp:
{alles}

Beantwoord voor elk element deze drie vragen. Meld alleen wat er FOUT is.

1. Staat het in het plan? Wijs de regel in de beschrijving, de endpoints of de
   tests aan die om dit endpoint, veld, statuscode of foutcode vraagt. Kun je
   die niet aanwijzen, dan is het verzonnen scope en moet het eruit.

2. Maakt de service dit antwoord zelf? Wijs de functie in het ontwerp aan die
   het produceert. Kun je die niet aanwijzen, dan komt het van FastAPI, van de
   middleware of van de webserver - en dan is de vorm ervan onbekend en mag een
   test er niets over asserten behalve de statuscode.

3. Test elke test gedrag of een implementatiedetail? Een test die object-
   identiteit, caching, interne datastructuren of private functies controleert,
   test het hoe in plaats van het wat. Die moet weg of herschreven worden naar
   het gedrag dat het plan noemt.

Beoordeel NIETS anders. Geen stijl, geen naamgeving, geen architectuur, geen
suggesties ter verbetering. Is er niets fout, zeg dat dan.

Antwoord met alleen JSON:
{{"ok": true}}
of
{{"ok": false, "problemen": [{{"path": "tests/test_logic.py", "probleem": "..."}}]}}"""

        print("[designer] ontwerpcontrole...", flush=True)
        try:
            oordeel = extract_json(
                self.llm.generate(prompt, role="spec_review", temperature=0.0),
                expect="object",
            )
        except Exception as e:
            # Een controle die de build sloopt is erger dan geen controle.
            print(f"[designer] ontwerpcontrole overgeslagen: {e}", flush=True)
            return specs

        if not oordeel or oordeel.get("ok") is not False:
            print("[designer] ontwerpcontrole: ok", flush=True)
            return specs

        problemen = [p for p in (oordeel.get("problemen") or []) if p.get("path") in specs]
        if not problemen:
            print("[designer] ontwerpcontrole: geen bruikbare bevindingen", flush=True)
            return specs

        per_pad: Dict[str, List[str]] = {}
        for p in problemen:
            per_pad.setdefault(p["path"], []).append(str(p.get("probleem", "")))

        print(f"[designer] ontwerpcontrole: {len(problemen)} probleem(en) in "
              f"{len(per_pad)} bestand(en)", flush=True)
        for pad, lijst in per_pad.items():
            for pr in lijst:
                print(f"           - {pad}: {pr}", flush=True)

        # Eenmalig herspecificeren. Geen lus: vindt de reviewer daarna nog iets,
        # dan vangt de tester het maar op.
        herstel = f"""{prompt}

=== GEVONDEN PROBLEMEN ===
{json.dumps(per_pad, indent=2, ensure_ascii=False)}

Herschrijf de specificaties van precies deze bestanden zodat de problemen
opgelost zijn: {json.dumps(list(per_pad), ensure_ascii=False)}
Haal weg wat verzonnen is, laat de rest ongemoeid, en verzin niets nieuws.

Antwoord met alleen JSON:
{{"bestanden": [{{"path": "...", "spec": "..."}}]}}"""
        try:
            data = extract_json(
                self.llm.generate(herstel, role=role, temperature=0.2),
                expect="object",
            )
        except Exception as e:
            print(f"[designer] herspecificatie mislukt ({e}), ontwerp blijft zoals het was",
                  flush=True)
            return specs

        for item in (data or {}).get("bestanden") or []:
            pad, spec = (item or {}).get("path"), (item or {}).get("spec")
            if pad in specs and spec:
                specs[pad] = spec if isinstance(spec, str) else json.dumps(
                    spec, indent=2, ensure_ascii=False
                )
                print(f"[designer] spec bijgesteld: {pad}", flush=True)
        return specs

    def _golven(self, paden: List[str]) -> List[List[str]]:
        """Contracten, dan de rest van src, dan de tests - en niets te groot.

        De volgorde is dezelfde die de developer aanhoudt, zodat een latere golf
        altijd de specs van waar hij op bouwt al binnen heeft.
        """
        contracten, bouw, tests = [], [], []
        for pad in paden:
            naam = pad.split("/")[-1]
            is_test = ("/tests/" in pad or pad.startswith("tests/")
                       or naam.startswith("test_") or naam == "conftest.py")
            if naam in CONTRACT_NAMEN:
                contracten.append(pad)
            elif is_test:
                tests.append(pad)
            else:
                bouw.append(pad)

        golven = []
        for groep in (contracten, bouw, tests):
            # Bovengrens per golf: een project met dertig testbestanden mag de
            # test-golf niet alsnog opblazen.
            for i in range(0, len(groep), MAX_PER_GOLF):
                stuk = groep[i:i + MAX_PER_GOLF]
                if stuk:
                    golven.append(stuk)
        return golven

    def _ontwerp(
        self,
        plan: Dict[str, Any],
        golf: List[str],
        eerdere_specs: Dict[str, str],
        feedback: Optional[Dict[str, Any]],
        role: str,
    ) -> Dict[str, str]:
        antwoord = self.llm.generate(
            self._prompt(plan, golf, feedback, eerdere_specs),
            role=role,
            temperature=0.2,
        )
        data = extract_json(antwoord, expect="object")
        if not data or not isinstance(data.get("bestanden"), list):
            raise ValueError(
                f"Designer: kon geen bruikbare JSON extraheren voor {golf} "
                f"(lengte {len(antwoord)}). Eerste 200 chars: {antwoord[:200]}"
            )

        specs = {}
        for item in data["bestanden"]:
            pad = (item or {}).get("path")
            spec = (item or {}).get("spec")
            if pad and spec:
                specs[pad] = spec if isinstance(spec, str) else json.dumps(
                    spec, indent=2, ensure_ascii=False
                )
        return specs

    def _prompt(
        self,
        plan: Dict[str, Any],
        paden: List[str],
        feedback: Optional[Dict[str, Any]],
        eerdere_specs: Optional[Dict[str, str]] = None,
    ) -> str:
        feedback_blok = ""
        if feedback:
            geschiedenis = "\n".join(feedback.get("history") or [])
            vorige = feedback.get("previous_files") or []
            vorige_code = "\n\n".join(
                f"--- {f['path']} ---\n{f.get('content','')}"
                for f in vorige
                if f.get("path") in set(paden)
            )
            feedback_blok = f"""
=== DIT IS EEN HERSTELRONDE ===
Er is al code geschreven en die faalt. Jouw taak is UITZOEKEN WAAROM en de
specificatie zo bijstellen dat het deze keer wel klopt. De schrijver die jouw
spec uitvoert denkt zelf niet na - alles wat er moet gebeuren moet dus in de
spec staan.

Wat er misging:
{feedback.get('summary', '')}

Issues:
{json.dumps(feedback.get('issues', []), indent=2, ensure_ascii=False)}

Testoutput (laatste 3000 tekens):
{(feedback.get('test_output') or '')[:3000]}

Eerdere pogingen in deze run:
{geschiedenis}

De huidige inhoud van de bestanden die je opnieuw moet specificeren:
{vorige_code}

Wees expliciet over wat er moet VERANDEREN en waarom. Noem de concrete
functie, het concrete veld, de concrete regel.
"""

        eerder_blok = ""
        if eerdere_specs:
            samen = "\n\n".join(
                f"--- {pad} ---\n{spec}" for pad, spec in eerdere_specs.items()
            )
            eerder_blok = f"""
=== AL ONTWORPEN BESTANDEN ===
Deze specs liggen vast. Sluit er exact op aan: gebruik de klassen, velden en
functies die hier staan en verzin er niets bij. Elk veld dat je in een test
assert MOET hierboven in het bijbehorende model staan.

{samen}
"""

        return f"""Je ontwerpt een Python-microservice tot op bestandsniveau. Je schrijft ZELF
geen code. Je levert per bestand een specificatie die zo concreet is dat een
eenvoudig model het kan uitschrijven zonder iets te hoeven bedenken.

Project: {plan['project_name']}
Beschrijving: {plan['description']}
Requirements: {json.dumps(plan['requirements'], indent=2)}
Endpoints: {json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}
Tests die moeten slagen: {json.dumps(plan['tests'], indent=2, ensure_ascii=False)}
{feedback_blok}
{eerder_blok}
{VASTE_KADERS}

Specificeer deze bestanden, in deze volgorde:
{json.dumps(paden, indent=2)}

Voor elk bestand geef je een spec die minstens dit bevat, voor zover van toepassing:
- waar het bestand voor dient, in een zin
- welke imports erin komen (exacte modulepaden)
- elke klasse: naam, basisklasse, en per veld de naam, het type en of het
  verplicht is. Gebruik StrictStr/StrictInt waar een test een 422 verwacht bij
  een verkeerd type - gewone str laat Pydantic stilzwijgend converteren.
- elke functie: exacte signature met types, wat hij doet, wat hij teruggeeft,
  en welke exception hij gooit bij welke situatie
- voor endpoints: pad, methode, request-model, response-model, statuscodes
- voor testbestanden: elke testfunctie bij naam, met wat hij aanroept en wat
  hij precies assert. Noem de concrete waarden.

Wees zo concreet dat twee verschillende schrijvers dezelfde code zouden
opleveren. Vage zinnen als "valideer de invoer" zijn onbruikbaar - schrijf op
WAT er gevalideerd wordt en WELKE fout eruit komt.

TWEE HARDE GRENZEN:

1. BLIJF BINNEN HET PLAN. Leg elk element dat je specificeert langs deze
   twee toetsen. Komt er een keer 'nee' uit, dan gaat het element eruit.

   TOETS A - staat het in het plan? Wijs de regel in de beschrijving, de
   endpoints of de tests aan die om dit element vraagt. Kun je die regel niet
   aanwijzen, dan is het jouw idee en niet de opdracht. Nuttig, netjes of
   gebruikelijk zijn geen redenen. Dit geldt voor endpoints, velden,
   statuscodes, foutcodes, tellers en elk stukje metadata in een response.

   TOETS B - maakt de service dit antwoord zelf? Wijs de functie in jouw eigen
   specificatie aan die dit antwoord produceert. Kun je die niet aanwijzen, dan
   komt het antwoord ergens anders vandaan - uit FastAPI, uit de middleware van
   het service_template, uit de webserver - en dan ken jij de vorm ervan niet.
   Specificeer die vorm dus niet en laat er geen test op asserten.

   Toets B is de belangrijkste, want daar gaat het telkens mis. Alles op
   transportniveau - content-type, JSON parsen, ontbrekende of verkeerd
   getypeerde velden, de limiet op de request body, timeouts, auth - wordt
   afgehandeld voor jouw code aan de beurt is. Dat een fout logisch bij jouw
   service hoort, betekent niet dat jouw code hem produceert.

   Wil een test toch controleren dat zo'n geval afgewezen wordt, assert dan
   alleen de statuscode en niets over de body.

2. WEES INTERN CONSISTENT. Elk veld dat een test assert MOET in het
   responsemodel van dat endpoint staan, met hetzelfde type. En andersom: elk
   veld in een responsemodel moet ergens vandaan komen. Loop je test-specs na
   tegen je model-specs voor je antwoordt - een test die een veld verwacht dat
   het model niet heeft, is een KeyError die je hier had kunnen zien.

Antwoord met alleen JSON:
{{"bestanden": [{{"path": "src/models.py", "spec": "..."}}]}}"""


# Vaste kaders waar het ontwerp zich aan moet houden. Los gehouden van de
# f-string omdat er voorbeeldcode met accolades in staat.
VASTE_KADERS = """
KADERS WAAR HET ONTWERP ZICH AAN MOET HOUDEN:

- Het project gebruikt het standaard service_template (staat al in
  src/service_template/). src/main.py bevat alleen:

      from src.service_template.bootstrap import create_app
      from src.routes import router as business_router

      app = create_app(
          title="<naam>",
          version="0.1.0",
          business_routers=[business_router],
      )

- Endpoints staan in src/routes.py als APIRouter. Nooit @app.get/@app.post in
  main.py.
- /health, /ready en /metrics komen automatisch uit het template. Niet zelf
  specificeren.
- Auth, CORS, rate limiting en security headers komen uit het template. Alleen
  specificeren dat een endpoint auth nodig heeft, niet hoe auth werkt:
      from src.service_template.auth import verify_bearer_token
- Source in src/, tests in tests/. Imports altijd "from src.X import Y", ook in
  tests. Nooit sys.path-trucs.
- Tests zijn pytest-functies met assert. De fixtures 'client' en 'auth_headers'
  komen uit tests/conftest.py.
- Coverage-gate is 80% van src/, met src/main.py en src/service_template/
  uitgesloten. Elke module met logica heeft dus tests nodig.
- Heeft de service module-level state, specificeer dan een reset_state()
  functie in die module, plus een autouse-fixture die hem aanroept - zowel in
  tests/conftest.py als bovenaan elk testbestand. reset_state gebruikt
  dict.clear() en 'global' voor tellers, geen rebind.
- Geen hardcoded secrets. Configuratie via os.getenv().
- Geen TODO's en geen placeholders in de spec.
"""
