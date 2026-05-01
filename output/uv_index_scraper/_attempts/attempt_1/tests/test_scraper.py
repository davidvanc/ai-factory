from unittest.mock import patch, Mock
from src.scraper import fetch_uv_index, parse_uv_index

def test_scraper_returns_valid_uv_index():
    html = "<html><body>UV-index: 5</body></html>"
    uv = parse_uv_index(html)
    assert isinstance(uv, int)
    assert uv == 5

def test_scraper_fallback_on_404():
    mock_response_404 = Mock()
    mock_response_404.status_code = 404
    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.text = "<html>UV index 8</html>"
    with patch('src.scraper.requests.get') as mock_get:
        mock_get.side_effect = [mock_response_404, mock_response_200]
        uv = fetch_uv_index()
        assert uv == 8
        assert mock_get.call_count == 2
        assert mock_get.call_args_list[0][0][0] == "https://www.meteo.be/nl/weer/verwachtingen/weer-voor-uccle"
        assert mock_get.call_args_list[1][0][0] == "https://www.meteo.be/en/weather/forecast/weather-for-uccle"