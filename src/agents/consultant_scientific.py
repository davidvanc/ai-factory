"""
Scientific Consultant — levert domeinkennis aan de Planner.
Gebruikt Gemini Pro voor de kennis (sterk in wetenschappelijke onderwerpen).
"""
import json
from src.llm.client import LLMClient


class ScientificConsultant:
    def __init__(self):
        self.llm = LLMClient()

    def consult(self, task: str) -> dict:
        prompt = f"""Je bent een wetenschappelijk consultant voor een software development team.
Een ontwikkelaar gaat dit project bouwen:

{task}

Geef de DOMEIN-KENNIS die de ontwikkelaar nodig heeft om dit goed te doen.
Focus op feiten, formules, terminologie, beperkingen en valkuilen.

Antwoord ALLEEN met dit JSON formaat:
{{
  "knowledge": "Bondige uitleg van de kern-concepten (max 300 woorden)",
  "formulas": [
    "Formule 1 met variabelen en eenheden",
    "Formule 2 ..."
  ],
  "key_facts": [
    "Belangrijk feit 1",
    "Belangrijk feit 2"
  ],
  "edge_cases": [
    "Edge case waar code mee moet omgaan",
    "..."
  ],
  "common_mistakes": [
    "Veel-gemaakte fout door programmeurs",
    "..."
  ],
  "recommended_libraries": [
    "library_name (waarvoor)",
    "..."
  ]
}}

Geen uitleg buiten het JSON object."""

        response = self.llm.generate(
            prompt,
            role="consultant_scientific",
            temperature=0.3,
            stream=False
        )

        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1:
            return {"knowledge": "", "error": "geen JSON gevonden"}

        try:
            return json.loads(response[start:end])
        except json.JSONDecodeError as e:
            return {"knowledge": response[:1000], "error": f"JSON parse: {e}"}

    def to_planner_context(self, consultation: dict) -> str:
        """Converteer naar tekst die in de Planner prompt geïnjecteerd wordt."""
        if "error" in consultation and "knowledge" not in consultation:
            return ""

        parts = ["=== WETENSCHAPPELIJKE CONTEXT (van Scientific Consultant) ==="]

        if consultation.get("knowledge"):
            parts.append(f"\n{consultation['knowledge']}")

        if consultation.get("formulas"):
            parts.append("\nFormules om te gebruiken:")
            for f in consultation["formulas"]:
                parts.append(f"  - {f}")

        if consultation.get("key_facts"):
            parts.append("\nBelangrijke feiten:")
            for f in consultation["key_facts"]:
                parts.append(f"  - {f}")

        if consultation.get("edge_cases"):
            parts.append("\nEdge cases om te testen:")
            for e in consultation["edge_cases"]:
                parts.append(f"  - {e}")

        if consultation.get("common_mistakes"):
            parts.append("\nVeel-gemaakte fouten om te vermijden:")
            for m in consultation["common_mistakes"]:
                parts.append(f"  - {m}")

        if consultation.get("recommended_libraries"):
            parts.append("\nAanbevolen Python libraries:")
            for lib in consultation["recommended_libraries"]:
                parts.append(f"  - {lib}")

        return "\n".join(parts)
