from src.who_standards import WHO_24H_PM25, WHO_24H_PM10


def test_who_24h_thresholds():
    assert WHO_24H_PM25 == 15
    assert WHO_24H_PM10 == 45
