import pytest
from src.statistics_calculator import calculate_statistics

def test_mean():
    result = calculate_statistics([1, 2, 3, 4, 5])
    assert result['mean'] == 3.0

def test_median_odd():
    result = calculate_statistics([1, 2, 3])
    assert result['median'] == 2.0

def test_median_even():
    result = calculate_statistics([1, 2, 3, 4])
    assert result['median'] == 2.5

def test_std():
    result = calculate_statistics([1, 2, 3, 4, 5])
    # Steekproef standaarddeviatie: sqrt(((1-3)^2+(2-3)^2+(3-3)^2+(4-3)^2+(5-3)^2)/4) = sqrt(10/4) = sqrt(2.5) ≈ 1.58113883
    assert abs(result['std'] - 1.5811388300841898) < 1e-9

def test_empty_list():
    with pytest.raises(ValueError, match="Lijst mag niet leeg zijn."):
        calculate_statistics([])

def test_non_numeric():
    with pytest.raises(TypeError, match="Alle elementen moeten numeriek zijn."):
        calculate_statistics([1, 'a', 3])
