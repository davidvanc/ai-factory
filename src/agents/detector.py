"""
Domain Detector — classificeert taken zodat de juiste consultant(s) ingezet worden.
Hybride: keyword matching first, LLM fallback bij twijfel.
"""
import json
from src.llm.client import LLMClient


# Keywords per domein - case insensitive matching
DOMAIN_KEYWORDS = {
    "scientific": [
        "bmi", "bmr", "calorie", "calorieën", "calories",
        "biology", "biologie", "biological", "medical", "medisch", "medisch advies",
        "health", "gezondheid", "physical health", "mental health",
        "physics", "fysica", "physical", "chemistry", "chemie", "chemical",
        "scientific", "wetenschappelijk", "wetenschap",
        "formula", "formule", "research", "onderzoek", "studie",
        "molecule", "dna", "rna", "protein", "eiwit","formule",
        "diagnosis", "diagnose", "drug", "medicatie", "medicijn", "dosage", "dosering",
        "statistical", "statistisch", "p-value", "correlation", "correlatie",
        "regression", "regressie", "hypothesis", "hypothese",
        "heart", "hart-", "cardiovascular", "cardio", "blood pressure", "bloeddruk",
        "cancer", "kanker", "tumor", "diabetes", "obesitas", "obesity",
        "vitamin", "vitamine", "mineral", "mineraal", "nutrition", "voeding",
        "anatomy", "anatomie", "physiology", "fysiologie",
        "epidemiology", "epidemiologie", "disease", "ziekte",
        "risk factor", "risicofactor", "mortality", "mortaliteit",
    ],
    "scraping": [
        "fanpage", "wiki", "wikipedia", "scrape", "scrapen", "crawl", "website",
        "haal van", "fetch from", "import from", "data van", "info over alle",
        "list of all", "lijst van alle", "episodes", "episode", "characters",
        "player stats", "player statistics", "live data", "actuele data",
        "actuele", "actual", "current", "huidige", "huidig",
        "news", "nieuws", "articles", "artikelen", "products from", "producten van",
        "weersvoorspelling", "weather forecast", "forecast", "voorspelling",
        "ophaalt", "ophalen", "downloaden van", "download from",
        "real-time", "realtime", "live",
    ],
}
    # "trading" voor later:
    # "trading": ["bot", "strategy", "backtest", "ohlcv", "rsi", "macd", "indicator", ...],



class DomainDetector:
    def __init__(self):
        self.llm = LLMClient()

    def _keyword_scan(self, task: str) -> dict:
        """Tel keyword matches per domein."""
        task_lower = task.lower()
        scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in task_lower]
            if matches:
                scores[domain] = {"score": len(matches), "matches": matches}
        return scores

    def _llm_classify(self, task: str) -> list:
        """Vraag LLM om classificatie - gebruikt voor onduidelijke gevallen."""
        prompt = f"""Classificeer deze software-taak in 0 of meer domeinen:

Taak: {task}

Domeinen:
- "scientific": vereist domein-specifieke kennis (medisch, biologie, chemie, fysica, wetenschap)
- "scraping": vereist live data van het web (info over actuele dingen, lijsten van real-world entiteiten)
- "general": geen specialiteit nodig (gewone code zoals algoritmes, CLI tools, simpele APIs)

Antwoord ALLEEN met een JSON array van labels, bv:
["scientific"] of ["scraping"] of ["scientific", "scraping"] of ["general"]

Geen uitleg, alleen de array."""

        response = self.llm.generate(prompt, role="judge", temperature=0.1, stream=False)

        # Parse JSON array
        from src.llm.json_utils import extract_json
        labels = extract_json(response, expect="array")
        if labels is None or not isinstance(labels, list):
            return ["general"]
        return labels
    def detect(self, task: str) -> dict:
        """
        Returns:
        {
          "domains": ["scientific", ...],
          "confidence": "high" | "medium" | "low",
          "method": "keywords" | "llm",
          "details": {...}
        }
        """
        keyword_scores = self._keyword_scan(task)

        # Hoge confidence: 2+ matches in een domein → keywords zijn genoeg
        strong_domains = [d for d, s in keyword_scores.items() if s["score"] >= 2]
        if strong_domains:
            return {
                "domains": strong_domains,
                "confidence": "high",
                "method": "keywords",
                "details": keyword_scores
            }

        # Geen matches: waarschijnlijk general
        if not keyword_scores:
            return {
                "domains": ["general"],
                "confidence": "high",
                "method": "keywords",
                "details": {}
            }

        # 1 match: niet zeker, vraag LLM
        llm_labels = self._llm_classify(task)
        return {
            "domains": llm_labels,
            "confidence": "medium",
            "method": "llm",
            "details": {"keyword_hints": keyword_scores, "llm_decision": llm_labels}
        }
