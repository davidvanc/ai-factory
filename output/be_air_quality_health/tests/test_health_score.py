import pytest
from src.health_score import calculate_health_score


def test_pm25_17_moderate_risk():
    result = calculate_health_score(17, 0)
    assert result["risk_level"] == "moderate"


def test_pm10_19_low_risk():
    result = calculate_health_score(0, 19)
    assert result["risk_level"] == "low"


def test_pm25_above_75_very_high_risk():
    result = calculate_health_score(76, 0)
    assert result["risk_level"] == "very high"


def test_score_between_0_and_100():
    result = calculate_health_score(50, 100)
    assert 0 <= result["score"] <= 100
    result2 = calculate_health_score(0, 0)
    assert 0 <= result2["score"] <= 100
    result3 = calculate_health_score(500, 500)
    assert result3["score"] == 100
