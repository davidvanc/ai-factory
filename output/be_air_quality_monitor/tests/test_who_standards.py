from src.who_standards import WHO_24H_PM10, get_exceedance_factor


def test_exceedance_factor():
    result = get_exceedance_factor(90, WHO_24H_PM10)
    assert result == 2.0
