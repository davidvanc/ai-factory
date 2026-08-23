"""
Zet de failures van een run om in lessen voor de memory-database.

De tabel `lessons` bestond al en de planner leest hem uit, maar `add_lesson`
werd nergens aangeroepen - na drie projecten met meerdere gefaalde pogingen
stond de teller nog op nul. Dit sluit dat gat.

De kunst zit in de korrelgrootte. Schrijf je de ruwe pytest-fout weg, dan krijg
je duizend unieke lessen die nooit terugkomen en die de planner-prompt
volspammen. Schrijf je te grof weg ("tests faalden"), dan zegt het niets.
Daarom vraagt dit een model om per run hooguit drie lessen die ook in een
ander project gelden, en wordt het patroon genormaliseerd zodat `add_lesson`
dezelfde les een tweede keer herkent en de teller ophoogt in plaats van te
dupliceren.
"""
import json
import re
from typing import Any, Dict, List

from src.llm.client import LLMClient
from src.llm.json_utils import extract_json

# Vaste woordenlijst. Vrije categorieen maken deduplicatie onmogelijk.
CATEGORIEEN = (
    "imports", "tests", "test-isolation", "api-contract", "validation",
    "state", "dependencies", "docker", "coverage", "judge-quality", "overig",
)

MAX_LESSEN = 3


def _normaliseer(patroon: str) -> str:
    """Zelfde les, zelfde sleutel. add_lesson dedupliceert op exacte tekst."""
    patroon = re.sub(r"\s+", " ", patroon or "").strip().rstrip(".")
    return patroon.lower()[:200]


def extraheer_lessen(
    task: str,
    plan: Dict[str, Any],
    failure_history: List[str],
    status: str,
    attempts: int,
) -> List[Dict[str, str]]:
    """Geeft een lijst {category, pattern, fix} terug. Leeg als er niets te leren valt."""
    if not failure_history:
        return []

    geschiedenis = "\n".join(failure_history)
    prompt = f"""Je leest de mislukte pogingen van een automatische code-generator en
destilleert daar lessen uit voor VOLGENDE projecten.

Opdracht die gedraaid werd: {task}
Project: {plan.get('project_name', '?')}
Eindresultaat: {status} na {attempts} poging(en)

Wat er misging per poging:
{geschiedenis}

Formuleer hooguit {MAX_LESSEN} lessen. Harde eisen:
- Een les moet in een ANDER project ook gelden. Niets over deze specifieke
  service, endpoints, veldnamen of functienamen.
- Kort: MAXIMAAL 15 woorden. Dit is een sleutel waarop dezelfde les een
  volgende keer herkend moet worden, geen uitleg. Schrijf hem als een regel,
  niet als een verhaal. De toelichting hoort in het fix-veld.
- Geen les die neerkomt op "schrijf correcte code" of "test beter".
- Valt er niets te leren dat generaliseert, geef dan een lege lijst terug.
  Dat is een prima antwoord - liever niets dan ruis.

Kies per les een categorie uit deze lijst: {", ".join(CATEGORIEEN)}

Antwoord met alleen JSON:
{{"lessen": [{{"category": "imports", "pattern": "...", "fix": "..."}}]}}
of
{{"lessen": []}}"""

    try:
        antwoord = LLMClient().generate(prompt, role="lesson_extractor", temperature=0.0)
        data = extract_json(antwoord, expect="object")
    except Exception as e:
        print(f"[memory] lesson-extractie overgeslagen: {e}")
        return []

    if not data:
        return []

    lessen = []
    for item in (data.get("lessen") or [])[:MAX_LESSEN]:
        patroon = _normaliseer(item.get("pattern", ""))
        if not patroon:
            continue
        categorie = item.get("category", "overig")
        if categorie not in CATEGORIEEN:
            categorie = "overig"
        fix = (item.get("fix") or "").strip()[:300] or None
        lessen.append({"category": categorie, "pattern": patroon, "fix": fix})
    return lessen
