import pytest
from src.stats import calculate_sum, calculate_average, calculate_max

def test_som():
    assert calculate_sum([1,2,3,4,5]) == 15

def test_gemiddelde():
    assert calculate_average([1,2,3,4,5]) == 3.0

def test_maximum():
    assert calculate_max([1,2,3,4,5]) == 5

def test_lege_lijst_som():
    with pytest.raises(ValueError, match="Lijst is leeg"):
        calculate_sum([])

def test_lege_lijst_gemiddelde():
    with pytest.raises(ValueError, match="Lijst is leeg"):
        calculate_average([])

def test_lege_lijst_max():
    with pytest.raises(ValueError, match="Lijst is leeg"):
        calculate_max([])
