import re
import json
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.meteo.be/nl/weer/verwachtingen/weer-voor-uccle",
    "https://www.meteo.be/en/weather/forecast/weather-for-uccle",
    "https://ozone.meteo.be/uv-index"
]

def parse_uv_index(html):
    soup = BeautifulSoup(html, 'lxml')
    # Use full HTML string to catch data attributes and inline text
    text = str(soup)
    match = re.search(r'UV[- ]index[^0-9]*([0-9]+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def fetch_uv_index():
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; uv-index-scraper/1.0)'
    }
    for url in URLS:
        try:
            response = requests.get(url, timeout=10, headers=headers)
            if response.status_code == 200:
                uv = parse_uv_index(response.text)
                if uv is not None:
                    return uv
        except requests.RequestException:
            continue

    # Fallback to Open-Meteo API (free, no key required)
    try:
        api_url = "https://api.open-meteo.com/v1/forecast?latitude=50.7963&longitude=4.3588&daily=uv_index_max&timezone=Europe/Brussels&forecast_days=1"
        resp = requests.get(api_url, timeout=10, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        uv = data['daily']['uv_index_max'][0]
        return uv
    except Exception:
        raise Exception("Kon de UV-index niet ophalen van alle bronnen.")
