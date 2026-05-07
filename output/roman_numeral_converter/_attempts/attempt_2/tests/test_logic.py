import pytest
from src.logic import int_to_roman, roman_to_int

def test_int_to_roman_valid():
    assert int_to_roman(1) == "I"
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(1994) == "MCMXCIV"
    assert int_to_roman(3999) == "MMMCMXCIX"

def test_int_to_roman_invalid():
    with pytest.raises(ValueError):
        int_to_roman(0)
    with pytest.raises(ValueError):
        int_to_roman(4000)
    with pytest.raises(ValueError):
        int_to_roman("123") # type: ignore

def test_roman_to_int_valid():
    assert roman_to_int("IV") == 4
    assert roman_to_int("MCMXCIV") == 1994
    assert roman_to_int("mcmxciv") == 1994

def test_roman_to_int_invalid():
    with pytest.raises(ValueError):
        roman_to_int("IIII")
    with pytest.raises(ValueError):
        roman_to_int("VIIII")
    with pytest.raises(ValueError):
        roman_to_int("")
    with pytest.raises(ValueError):
        roman_to_int("ABC")
