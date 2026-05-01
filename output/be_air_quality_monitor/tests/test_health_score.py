import json
from src.health_score import get_health_score
from src.report import generate_report


def test_score_range():
    result = get_health_score(10, 20)
    assert 0 <= result['score'] <= 100
    result2 = get_health_score(50, 100)
    assert result2['score'] == 100
    result3 = get_health_score(0, 0)
    assert result3['score'] == 0


def test_classification_good():
    result = get_health_score(3, 10)
    assert result['classification'] == "Goed"


def test_classification_very_unhealthy():
    result = get_health_score(30, 40)
    assert result['classification'] == "Zeer ongezond"


def test_generate_report_json():
    report = generate_report("Brussel", 12.3, 25.1, 50, "Matig")
    assert "timestamp" in report
    assert report["location"] == "Brussel"
    assert report["pm2_5"] == 12.3
    assert report["pm10"] == 25.1
    assert report["risk_score"] == 50
    assert report["classification"] == "Matig"
    json_str = json.dumps(report)
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed == report
