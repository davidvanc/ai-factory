"""
Scraper Consultant — haalt LIVE web data op om de Planner te informeren.
Gebruikt DeepSeek voor reasoning + Firecrawl voor scraping.
"""
import os
import json
from src.llm.client import LLMClient


class ScraperConsultant:
    def __init__(self):
        self.llm = LLMClient()
        self.firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        if not self.firecrawl_key:
            raise ValueError("FIRECRAWL_API_KEY niet gevonden in .env")

    def _identify_sources(self, task: str) -> dict:
        prompt = f"""Een ontwikkelaar gaat dit project bouwen, en heeft live web data nodig:

{task}

Genereer een SEARCH QUERY die een zoekmachine zou geven naar de juiste pagina's.

KRITISCHE REGELS:

1. PREFEREER PUBLIEKE WEBSITES boven API's
   - Goed: kmi.be, meteo.be, statbel.fgov.be, wikipedia.org, government sites
   - Slecht: api.x.com endpoints (vaak betalend, vereisen keys, sterven)
   - Pas op voor "API as a service" sites (waqi.info, openweathermap, openaq)

2. ALLEEN OFFICIËLE / GRATIS BRONNEN
   - Overheidsdiensten (KMI, FOD, EPA, NOAA, EU agencies)
   - Wetenschappelijke instellingen (universiteiten, onderzoek instituten)
   - Wikipedia voor algemene info
   - Open-Meteo (echt gratis weer-API zonder key)

3. GEEN URLs VERZINNEN
   - Geef alleen specific_urls als je 100% zeker bent
   - Twijfel je? Laat leeg en focus op search_query
   - search_query moet woorden bevatten die op de doelpagina staan

4. SEARCH QUERY TIPS
   - Voeg "site:overheid.be" of "site:gov" toe als je specifiek officiële bronnen wil
   - Voeg "scrape" of "html table" NIET toe (gebruiker wil data, niet hoe te scrapen)
   - Maximaal 8 woorden

Antwoord ALLEEN met dit JSON:
{{
  "search_query": "korte search opdracht (verplicht)",
  "specific_urls": [],
  "data_to_extract": [
    "veld 1",
    "veld 2"
  ],
  "expected_volume": "small | medium | large"
}}

Geen uitleg buiten het JSON."""

        response = self.llm.generate(
            prompt,
            role="developer",
            temperature=0.2,
            stream=False
        )

        from src.llm.json_utils import extract_json
        result = extract_json(response, expect="object")
        if result is None:
            return {"search_query": task[:60], "specific_urls": [], "data_to_extract": [], "expected_volume": "small"}
        return result

    def _firecrawl_search(self, query: str, limit: int = 5) -> list:
        """Zoek + scrape: search levert URLs, daarna scrape we de top resultaten."""
        from firecrawl import Firecrawl
        app = Firecrawl(api_key=self.firecrawl_key)
        try:
            search_result = app.search(query, limit=limit)
            # SearchData heeft .web attribute met lijst van resultaten
            web_results = getattr(search_result, "web", []) or []

            normalized = []
            for hit in web_results[:limit]:
                url = getattr(hit, "url", "")
                title = getattr(hit, "title", "")
                if not url:
                    continue
                # Search levert alleen description - we scrapen de URL voor volledige content
                scraped = self._firecrawl_scrape(url)
                if scraped.get("markdown"):
                    normalized.append({
                        "url": url,
                        "title": title or scraped.get("title", ""),
                        "markdown": scraped["markdown"]
                    })
            return normalized
        except Exception as e:
            print(f"[scraper] search error: {e}")
            return []

    def _firecrawl_scrape(self, url: str) -> dict:
        from firecrawl import Firecrawl
        app = Firecrawl(api_key=self.firecrawl_key)
        try:
            result = app.scrape(url, formats=["markdown"])
            if isinstance(result, dict):
                markdown = result.get("markdown", "")
                meta = result.get("metadata", {}) if isinstance(result.get("metadata"), dict) else {}
                title = meta.get("title", "")
            else:
                markdown = getattr(result, "markdown", "") or ""
                meta = getattr(result, "metadata", None)
                title = ""
                if meta:
                    if isinstance(meta, dict):
                        title = meta.get("title", "")
                    else:
                        title = getattr(meta, "title", "")
            return {
                "url": url,
                "markdown": (markdown or "")[:5000],
                "title": title or ""
            }
        except Exception as e:
            return {"url": url, "markdown": "", "error": str(e)}

    def consult(self, task: str, max_pages: int = 5) -> dict:
        sources = self._identify_sources(task)
        print(f"[scraper] zoekopdracht: {sources.get('search_query', '')}")

        scraped = []
        used_credits = 0

        for url in sources.get("specific_urls", [])[:max_pages]:
            print(f"[scraper] scrape: {url}")
            result = self._firecrawl_scrape(url)
            if result.get("markdown"):
                scraped.append(result)
                used_credits += 1

        remaining = max_pages - len(scraped)
        if remaining > 0 and sources.get("search_query"):
            search_results = self._firecrawl_search(sources["search_query"], limit=remaining)
            for hit in search_results[:remaining]:
                if hit.get("markdown"):
                    scraped.append({
                        "url": hit.get("url", ""),
                        "markdown": hit.get("markdown", "")[:5000],
                        "title": hit.get("title", "")
                    })
                    used_credits += 1

        return {
            "sources": sources,
            "pages_scraped": scraped,
            "page_count": len(scraped),
            "credits_used": used_credits
        }

    def to_planner_context(self, consultation: dict) -> str:
        if consultation.get("page_count", 0) == 0:
            return ""

        parts = ["=== LIVE WEB DATA (van Scraper Consultant) ==="]
        parts.append(f"Bronnen geïdentificeerd: {consultation['sources'].get('search_query', '')}")
        parts.append(f"Pagina's gescraped: {consultation['page_count']}")
        parts.append("\nGeëxtraheerde data:")

        for i, page in enumerate(consultation.get("pages_scraped", []), 1):
            parts.append(f"\n--- Pagina {i}: {page.get('title', page.get('url', 'unknown'))} ---")
            parts.append(f"URL: {page.get('url', '')}")
            content = page.get("markdown", "")[:2000]
            parts.append(content)

        parts.append(f"\n[scraper consultant gebruikt {consultation.get('credits_used', 0)} Firecrawl credits]")
        return "\n".join(parts)
