import re
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.meteo.be/nl/weer/verwachtingen/weer-voor-uccle",
    "https://www.meteo.be/en/weather/forecast/weather-for-uccle",
    "https://ozone.meteo.be/uv-index"
]

def parse_uv_index(html):
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text()
    match = re.search(r'UV[- ]index[^0-9]*([0-9]+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def fetch_uv_index():
    for url in URLS:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                uv = parse_uv_index(response.text)
                if uv is not None:
                    return uv
        except requests.RequestException:
            continue
    raise Exception("Kon de UV-index niet ophalen van alle bronnen.")