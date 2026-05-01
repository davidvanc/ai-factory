import pytest
import responses
from src.data_fetcher import fetch_aqicn
from src.main import get_air_quality, process_cities


@responses.activate
def test_fetch_aqicn_parses_values(monkeypatch):
    monkeypatch.setenv('AQICN_TOKEN', 'test_token')
    mock_response = {
        "status": "ok",
        "data": {
            "aqi": 60,
            "iaqi": {
                "pm25": {"v": 18.5},
                "pm10": {"v": 32.1}
            }
        }
    }
    responses.add(
        responses.GET,
        "https://api.waqi.info/feed/Brussel/?token=test_token",
        json=mock_response,
        status=200
    )
    result = fetch_aqicn("Brussel")
    assert result['pm2_5'] == 18.5
    assert result['pm10'] == 32.1


def test_main_fallback_to_openaq(mocker):
    mock_aqicn = mocker.patch('src.data_fetcher.fetch_aqicn', side_effect=Exception("API down"))
    mock_openaq = mocker.patch('src.data_fetcher.fetch_openaq', return_value={'pm2_5': 10.0, 'pm10': 20.0})
    result = get_air_quality("Brussel")
    assert result == {'pm2_5': 10.0, 'pm10': 20.0}
    mock_aqicn.assert_called_once_with("Brussel")
    mock_openaq.assert_called_once_with("Brussel")


def test_process_multiple_cities(mocker):
    side_effect = [
        {'pm2_5': 5.0, 'pm10': 10.0},
        {'pm2_5': 8.0, 'pm10': 15.0},
        {'pm2_5': 12.0, 'pm10': 20.0},
        {'pm2_5': 3.0, 'pm10': 8.0}
    ]
    mocker.patch('src.data_fetcher.fetch_aqicn', side_effect=side_effect)
    reports = process_cities(["Brussel", "Antwerpen", "Gent", "Luik"])
    assert len(reports) == 4
    cities = [r['location'] for r in reports]
    assert "Brussel" in cities
    assert "Antwerpen" in cities
    assert "Gent" in cities
    assert "Luik" in cities
    brussel = next(r for r in reports if r['location'] == "Brussel")
    assert brussel['pm2_5'] == 5.0
    assert brussel['risk_score'] == 20
    assert brussel['classification'] == "Matig"
