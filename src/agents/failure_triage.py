"""
Beoordeelt bij een gefaalde test of de fout in de code zit of in de test.

Waarom dit bestaat. De pipeline behandelde het oordeel van de tester als de
waarheid: `passed: False` betekende "code stuk", punt. Op 2026-08-23 kostte dat
zes euro aan een IBAN-service die vier pogingen op rij alle unit- en
integratietests haalde en telkens struikelde over een smoke test die
/countries/{country_code} letterlijk opvroeg - met accolades. De service gaf
correct 404 op een land dat zo heet. Er was geen enkele stap die vroeg of die
test wel klopte, en de designer-prompt eiste bovendien dat er iets VERANDERDE.
Dus veranderde er elke ronde iets, voor ~1,50 dollar per keer.

Dit is de stap die een menselijke developer wel zet: kijken naar de fout en
vaststellen dat het verzoek nergens op sloeg.

DE VEILIGHEIDSKLEP IS HET BELANGRIJKSTE ONDERDEEL. Een model dat zich uit elke
falende test mag praten keurt vroeg of laat kapotte code goed, en dat is veel
erger dan wat we nu hebben. Daarom mag "de test is fout" alleen als er concreet
aangewezen wordt WAT er niet klopt aan het verzoek of de assertie. Kan het dat
niet, dan is het oordeel "de code is fout". Twijfel valt altijd in het nadeel
van de code.
"""
import json
from typing import Any, Dict, List

from src.llm.client import LLMClient
from src.llm.json_utils import extract_json


def beoordeel_fouten(
    plan: Dict[str, Any],
    falende: List[Dict[str, str]],
    bestanden: List[Dict[str, str]],
) -> Dict[str, Dict[str, str]]:
    """Geeft {naam: {"oordeel": "code"|"test", "reden": ...}} terug.

    Alles wat niet expliciet en onderbouwd als "test" wordt aangemerkt, telt als
    "code". Bij twijfel, bij een lege lijst of bij een fout in de aanroep krijgt
    de code dus de schuld - dat is de veilige kant.
    """
    if not falende:
        return {}

    # Alleen de bestanden die ertoe doen, anders wordt de prompt onnodig groot.
    relevant = [f for f in bestanden if f.get("path", "").startswith(("src/", "tests/"))]
    code = "\n\n".join(
        f"--- {f['path']} ---\n{f.get('content', '')[:4000]}" for f in relevant[:12]
    )

    lijst = "\n".join(
        f"- {f.get('naam', '?')}: {f.get('reden', '')}" for f in falende
    )

    prompt = f"""Een automatisch gegenereerde service faalt op een of meer tests. Bepaal per
falende test of de fout in de CODE zit of in de TEST.

Wat de service moet doen:
{plan.get('description', '')}

Endpoints volgens het plan:
{json.dumps(plan.get('endpoints', []), indent=2, ensure_ascii=False)}

Falende tests:
{lijst}

De code:
{code}

Oordeel "test" mag je ALLEEN geven als je concreet kunt aanwijzen wat er niet
klopt aan het verzoek of de assertie zelf. Bijvoorbeeld:
- er staat een niet-ingevulde padparameter in de URL, zoals /landen/{{code}}
- er wordt een header of body meegestuurd die niet bij dit endpoint hoort
- de test controleert object-identiteit, interne datastructuren of een private
  functie in plaats van het gedrag dat het plan beschrijft
- de test verwacht een responsvorm van een fout die niet door deze code
  geproduceerd wordt maar door het framework

In ALLE andere gevallen is het oordeel "code". Kun je niet precies aanwijzen wat
er mis is met de test, dan is het "code". Een test die streng is, ongemakkelijk
is of een randgeval afdekt, is niet fout - die doet zijn werk.

Antwoord met alleen JSON:
{{"oordelen": [{{"naam": "...", "oordeel": "code", "reden": "..."}}]}}"""

    try:
        data = extract_json(
            LLMClient().generate(prompt, role="failure_triage", temperature=0.0),
            expect="object",
        )
    except Exception as e:
        print(f"[triage] overgeslagen ({e}) - alle fouten tellen als code", flush=True)
        return {}

    uitslag = {}
    for item in (data or {}).get("oordelen") or []:
        naam = (item or {}).get("naam")
        oordeel = (item or {}).get("oordeel")
        reden = str((item or {}).get("reden", "")).strip()
        if not naam or oordeel not in ("code", "test"):
            continue
        # Zonder onderbouwing telt "test" niet mee.
        if oordeel == "test" and len(reden) < 20:
            oordeel = "code"
            reden = "als test aangemerkt zonder onderbouwing, telt daarom als code"
        uitslag[naam] = {"oordeel": oordeel, "reden": reden}
    return uitslag
