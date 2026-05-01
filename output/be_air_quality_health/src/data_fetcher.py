import requests
from src.config import IRCEL_BASE_URL, OPENDATA_BRUSSELS_URL, AQICN_TOKEN


class DataFetchError(Exception):
    pass


# Mapping of Belgian cities to IRCEL station codes (example codes)
CITY_STATION_MAP = {
    "brussels": "BR001",
    "antwerp": "AN001",
    "ghent": "GN001",
    "charleroi": "CR001",
    "liege": "LG001",
    "bruges": "BG001",
    "namur": "NA001",
    "leuven": "LV001",
    "mons": "MN001",
    "aalst": "AL001",
}


def _fetch_ircel(city: str) -> dict:
    station = CITY_STATION_MAP.get(city.lower())
    if not station:
        raise DataFetchError(f"No IRCEL station for {city}")
    url = f"{IRCEL_BASE_URL}/measurements?station={station}&parameter=PM25,PM10"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    pm25 = None
    pm10 = None
    for m in data:
        if m.get("parameter") == "PM25":
            pm25 = m.get("value")
        elif m.get("parameter") == "PM10":
            pm10 = m.get("value")
    if pm25 is None or pm10 is None:
        raise DataFetchError("Missing PM data from IRCEL")
    return {"pm25": pm25, "pm10": pm10}


def _fetch_aqicn(city: str) -> dict:
    token = AQICN_TOKEN
    if not token:
        raise DataFetchError("AQICN token not configured")
    url = f"https://api.waqi.info/feed/{city}/?token={token}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "ok":
        raise DataFetchError("AQICN API error")
    iaqi = data["data"]["iaqi"]
    pm25 = iaqi.get("pm25", {}).get("v")
    pm10 = iaqi.get("pm10", {}).get("v")
    if pm25 is None or pm10 is None:
        raise DataFetchError("Missing PM data from AQICN")
    return {"pm25": pm25, "pm10": pm10}


def _fetch_opendata(city: str) -> dict:
    if city.lower() != "brussels":
        raise DataFetchError("OpenData Brussels only available for Brussels")
    url = f"{OPENDATA_BRUSSELS_URL}?dataset=air-quality-measurements&q=brussels&rows=1"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    records = data.get("records", [])
    if not records:
        raise DataFetchError("No data from OpenData Brussels")
    fields = records[0].get("fields", {})
    pm25 = fields.get("pm25")
    pm10 = fields.get("pm10")
    if pm25 is None or pm10 is None:
        raise DataFetchError("Missing PM data from OpenData Brussels")
    return {"pm25": pm25, "pm10": pm10}


def fetch_pm_data(city: str) -> dict:
    fetchers = [
        _fetch_ircel,
        _fetch_aqicn,
        _fetch_opendata,
    ]
    for fetcher in fetchers:
        try:
            result = fetcher(city)
            if result is not None:
                return result
        except Exception:
            continue
    raise DataFetchError(f"Could not fetch air quality data for {city}")
