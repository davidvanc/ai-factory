import pytest
from unittest.mock import patch
from src.main import generate_report, CityNotFoundError
from src.data_fetcher import DataFetchError


def test_generate_report_returns_dict():
    with patch('src.main.fetch_pm_data') as mock_fetch:
        mock_fetch.return_value = {"pm25": 10.0, "pm10": 20.0}
        report = generate_report("brussels")
        assert isinstance(report, dict)
        assert report["city"] == "brussels"
        assert report["pm25"] == 10.0
        assert report["pm10"] == 20.0
        assert "score" in report
        assert "risk_level" in report


def test_unknown_city_raises_error():
    with patch('src.main.fetch_pm_data') as mock_fetch:
        mock_fetch.side_effect = DataFetchError("No data")
        with pytest.raises(CityNotFoundError, match="No data available for city"):
            generate_report("unknown")
