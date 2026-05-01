import pytest
import responses
from src.data_fetcher import fetch_pm_data, DataFetchError, CITY_STATION_MAP
from src.config import IRCEL_BASE_URL


@responses.activate
def test_fetch_ircel_success():
    city = "brussels"
    station = CITY_STATION_MAP[city]
    url = f"{IRCEL_BASE_URL}/measurements?station={station}&parameter=PM25,PM10"
    mock_data = [
        {"parameter": "PM25", "value": 12.5, "unit": "µg/m³"},
        {"parameter": "PM10", "value": 20.0, "unit": "µg/m³"}
    ]
    responses.add(responses.GET, url, json=mock_data, status=200)
    result = fetch_pm_data(city)
    assert result == {"pm25": 12.5, "pm10": 20.0}


@responses.activate
def test_fallback_to_aqicn(monkeypatch):
    monkeypatch.setenv("AQICN_TOKEN", "dummy_token")
    city = "antwerp"
    # IRCEL fails
    station = CITY_STATION_MAP.get(city)
    ircel_url = f"{IRCEL_BASE_URL}/measurements?station={station}&parameter=PM25,PM10"
    responses.add(responses.GET, ircel_url, status=500)
    # AQICN succeeds
    aqicn_url = f"https://api.waqi.info/feed/{city}/?token=dummy_token"
    aqicn_response = {
        "status": "ok",
        "data": {
            "iaqi": {
                "pm25": {"v": 15.0},
                "pm10": {"v": 30.0}
            }
        }
    }
    responses.add(responses.GET, aqicn_url, json=aqicn_response, status=200)
    result = fetch_pm_data(city)
    assert result == {"pm25": 15.0, "pm10": 30.0}


@responses.activate
def test_unknown_city(monkeypatch):
    monkeypatch.setenv("AQICN_TOKEN", "dummy_token")
    city = "unknown_city"
    # IRCEL will raise because city not in map (no HTTP request)
    # AQICN will be tried, mock it to return error
    aqicn_url = f"https://api.waqi.info/feed/{city}/?token=dummy_token"
    responses.add(responses.GET, aqicn_url, json={"status": "error"}, status=200)
    # OpenData Brussels will raise because city != brussels
    with pytest.raises(DataFetchError, match="Could not fetch air quality data"):
        fetch_pm_data(city)
