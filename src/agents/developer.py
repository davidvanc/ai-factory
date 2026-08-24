"""
Developer-agent: schrijft de code voor een gepland project.

Twee fasen, en dat is de kern van dit bestand.

FASE 1 - ontwerpen (duur model, een keer). De DesignerAgent denkt het hele
project door en legt per bestand vast wat erin moet: functies, signatures,
gedrag, fouten, imports, en per test wat er precies geassert wordt.

FASE 2 - uitschrijven (goedkoop model, per bestand). Een model dat NIET
redeneert zet die specificatie om in code. Het hoeft niets te bedenken.

Waarom zo. Eerder schreef deze agent per bestand met een sterk model, waarbij
elk bestand de volledige opdracht meekreeg en opnieuw over het hele probleem
nadacht. Gemeten op een base64-service: 19 aanroepen, 89% van alle
output-tokens ging naar redeneren, en de zwaarste aanroep gebruikte 35.606
tokens om 3.256 tekens code op te leveren. Daarvoor liep de agent op een
JSON-blob voor het hele project, die tegen de max_tokens-grens aanliep en dan
alles verloor.

Het denkwerk gebeurt nu een keer in plaats van per bestand, en het typewerk
gaat naar een model dat honderd keer minder kost. Ook bij een retry wordt er
opnieuw ontworpen, niet alleen opnieuw geschreven: een niet-redenerend model
kan een bug niet bedenken.
"""
import json
from typing import Optional, Dict, Any, List

from src.llm.client import LLMClient
from src.llm.json_utils import extract_json
from src.agents.designer import DesignerAgent

# Bestanden die contracten vastleggen waar de rest zich aan moet houden.
# Die gaan eerst, zodat latere bestanden ze letterlijk in hun context krijgen.
CONTRACT_BESTANDEN = (
    "constants.py", "types.py", "errors.py", "config.py", "models.py", "schemas.py",
)

# Foutmeldingen die zeggen "de afspraak zelf klopt niet", niet "deze regel is fout".
CONTRACT_SIGNALEN = (
    "importerror", "modulenotfounderror", "attributeerror", "nameerror",
    "has no attribute", "unexpected keyword argument", "cannot import name",
    "validation error", "field required", "is not defined",
)

# Bestanden die geen model nodig hebben. Een lege __init__.py liet zich eerder
# een volledige LLM-aanroep kosten, inclusief redeneren.
VASTE_INHOUD = {
    "__init__.py": "",
}


class DeveloperAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.designer = DesignerAgent()

    # =========================
    # PUBLIEKE API (ongewijzigd contract met de pipeline)
    # =========================

    def run(
        self,
        plan: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None,
        role_override: str = "developer",
    ) -> Dict[str, Any]:
        premium = role_override == "developer_premium"
        designer_rol = "designer_premium" if premium else "designer"
        schrijver_rol = "writer_premium" if premium else "writer"

        paden = self._bestandsvolgorde(plan)
        if not paden:
            raise ValueError("Developer: het plan bevat geen 'structure' met bestandspaden")

        vorige = {
            f["path"]: f.get("content", "")
            for f in (feedback or {}).get("previous_files", [])
            if f.get("path")
        }
        opnieuw = self._te_herschrijven(paden, vorige, feedback)

        # Triviale bestanden hoeven geen spec en geen model.
        te_ontwerpen = [p for p in paden if p in opnieuw and not self._vaste_inhoud(p)]

        print(f"[developer] ontwerpronde voor {len(te_ontwerpen)} bestand(en) "
              f"via rol '{designer_rol}'", flush=True)
        specs = self.designer.run(plan, te_ontwerpen, feedback=feedback, role=designer_rol)

        geschreven: List[Dict[str, str]] = []
        hergebruikt = [p for p in paden if p not in opnieuw and p in vorige]
        if hergebruikt:
            print(f"[developer] {len(hergebruikt)} bestand(en) ongewijzigd overgenomen",
                  flush=True)

        gecontroleerd = False
        nieuw_contract = False

        for i, pad in enumerate(paden, 1):
            if pad not in opnieuw and pad in vorige:
                geschreven.append({"path": pad, "content": vorige[pad]})
                continue

            vast = self._vaste_inhoud(pad)
            if vast is not None:
                geschreven.append({"path": pad, "content": vast})
                continue

            # Zodra de contracten staan en er iets op gebouwd gaat worden:
            # eerst controleren. Daarna is corrigeren veel duurder, want dan
            # heeft alles zich er al naar gevormd.
            if not gecontroleerd and self._is_bouwbestand(pad) and nieuw_contract:
                geschreven = self._controleer_contracten(plan, geschreven, schrijver_rol, specs)
                gecontroleerd = True

            print(f"[developer] bestand {i}/{len(paden)}: {pad}", flush=True)
            inhoud = self.llm.generate(
                self._schrijfprompt(pad, specs.get(pad), geschreven, plan),
                role=schrijver_rol,
                temperature=0.1,
            )
            inhoud = self._strip_fences(inhoud)
            if not inhoud.strip():
                raise ValueError(f"Developer: leeg antwoord voor {pad}")
            geschreven.append({"path": pad, "content": inhoud})
            if self._is_contract(pad):
                nieuw_contract = True

        return {"files": geschreven}

    # =========================
    # SCHRIJFPROMPT (gaat naar het goedkope model)
    # =========================

    def _schrijfprompt(
        self,
        pad: str,
        spec: Optional[str],
        geschreven: List[Dict[str, str]],
        plan: Dict[str, Any],
    ) -> str:
        """Zo min mogelijk om over na te denken: een spec en de bestaande code."""
        context = ""
        if geschreven:
            relevant = geschreven[-8:]  # meer dan dit heeft een schrijver niet nodig
            blokken = "\n\n".join(f"--- {f['path']} ---\n{f['content']}" for f in relevant)
            context = (
                "\n=== AL GESCHREVEN BESTANDEN ===\n"
                "Importeer hieruit wat je nodig hebt. Verzin geen namen die hier "
                "niet in staan. Herhaal deze bestanden niet.\n\n" + blokken + "\n"
            )

        if spec:
            opdracht = f"=== SPECIFICATIE VAN {pad} ===\n{spec}\n"
        else:
            # Vangnet als de designer dit bestand oversloeg.
            opdracht = (
                f"=== {pad} ===\n"
                f"Er is geen specificatie voor dit bestand. Leid uit het plan af wat "
                f"erin hoort.\nProject: {plan.get('description', '')}\n"
            )

        return f"""Je schrijft exact een bestand van een Python-microservice uit een kant-en-klare
specificatie. Bedenk niets zelf: alles wat je moet weten staat hieronder.

Vaste kaders:
- source in src/, tests in tests/, PYTHONPATH is /app
- imports altijd "from src.X import Y", ook in tests, nooit sys.path-trucs
- tests zijn pytest-functies met assert; 'client' en 'auth_headers' zijn
  fixtures uit tests/conftest.py
- geen TODO's, geen placeholders, geen halve functies
- geen hardcoded secrets, configuratie via os.getenv()
{context}
{opdracht}
Schrijf nu {pad}.

Antwoord met ALLEEN de volledige inhoud van dat bestand. Geen uitleg vooraf of
achteraf, geen markdown code fences, geen bestandsnaam als kop, geen JSON.
Begin direct met de eerste regel van het bestand."""

    # =========================
    # WELKE BESTANDEN, IN WELKE VOLGORDE
    # =========================

    @staticmethod
    def _vaste_inhoud(pad: str) -> Optional[str]:
        return VASTE_INHOUD.get(pad.split("/")[-1])

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
        tekst = " ".join([
            str(feedback.get("summary", "")),
            json.dumps(feedback.get("issues", []), ensure_ascii=False),
            str(feedback.get("test_output", "") or ""),
        ]).lower()

        if genoemd:
            opnieuw = {p for p in paden if p in set(genoemd)}
        else:
            opnieuw = {
                p for p in paden
                if p.split("/")[-1].lower() in tekst or p.lower() in tekst
            }

        opnieuw |= {p for p in paden if p not in vorige}

        # Ruikt het naar een contractprobleem, dan zijn de contracten verdacht -
        # ook als hun naam nergens in de traceback staat.
        if any(sig in tekst for sig in CONTRACT_SIGNALEN):
            contracten = {p for p in paden if self._is_contract(p)}
            if contracten - opnieuw:
                print("[developer] contractsignaal in de testoutput: "
                      "contractbestanden gaan mee in de herschrijfset", flush=True)
            opnieuw |= contracten

        # Hier stond: vanaf de derde poging alles opnieuw. Die regel komt uit de
        # tijd dat de developer zelf schreef, toen "alles opnieuw" een aanroep
        # was. In de twee-fasen-opzet betekent het een volledige ontwerpronde op
        # Opus, en in golvenmodus zelfs drie. Gemeten op de IBAN-taak: 14
        # designer-aanroepen en 315.381 tokens in een run van 11,89 dollar.
        #
        # De herhalingsrem in de pipeline vangt inmiddels af waar deze regel
        # voor bedoeld was: drie keer dezelfde fout stopt de run. Alles opnieuw
        # schrijven voegt daar niets aan toe behalve kosten, en gooide in een
        # eerdere run vier rondes werkende code weg.
        return opnieuw or set(paden)

    # =========================
    # CONTRACTCONTROLE
    # =========================

    @staticmethod
    def _is_contract(pad: str) -> bool:
        return pad.split("/")[-1] in CONTRACT_BESTANDEN

    @staticmethod
    def _is_bouwbestand(pad: str) -> bool:
        naam = pad.split("/")[-1]
        return naam != "__init__.py" and naam not in CONTRACT_BESTANDEN

    def _controleer_contracten(
        self,
        plan: Dict[str, Any],
        geschreven: List[Dict[str, str]],
        schrijver_rol: str,
        specs: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Houdt de contractbestanden tegen het plan voor de rest erop gebouwd wordt.

        Een fout contract is de duurste soort fout in deze opzet: elk volgend
        bestand krijgt het letterlijk mee en plooit zich ernaar, tests incluis.
        Zo'n project komt door de tester heen en is toch verkeerd.
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

Beoordeel NIET de stijl, de naamgeving of de implementatie.

Antwoord met alleen JSON:
{{"ok": true}}
of
{{"ok": false, "problemen": ["concreet probleem 1"]}}"""

        print("[developer] contractcontrole...", flush=True)
        try:
            oordeel = extract_json(
                self.llm.generate(prompt, role="contract_review", temperature=0.0),
                expect="object",
            )
        except Exception as e:
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

        hersteld = []
        for f in geschreven:
            if not self._is_contract(f["path"]):
                hersteld.append(f)
                continue
            herstel = f"""{prompt}

=== GEVONDEN PROBLEMEN ===
{json.dumps(problemen, indent=2, ensure_ascii=False)}

=== OORSPRONKELIJKE SPECIFICATIE VAN {f['path']} ===
{specs.get(f['path'], '(geen)')}

Herschrijf {f['path']} zodat deze problemen opgelost zijn. Wijzig niets anders.
Antwoord met ALLEEN de volledige inhoud van {f['path']}, geen uitleg, geen fences."""
            try:
                nieuwe = self._strip_fences(
                    self.llm.generate(herstel, role=schrijver_rol, temperature=0.1)
                )
                hersteld.append({"path": f["path"], "content": nieuwe or f["content"]})
            except Exception as e:
                print(f"[developer] herstel van {f['path']} mislukt ({e}), "
                      f"oorspronkelijke versie blijft staan", flush=True)
                hersteld.append(f)
        return hersteld

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
