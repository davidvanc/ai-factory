import pytest
from src.logic import clean_hex, hex_to_rgb, hex_to_hsl

def test_clean_hex():
    assert clean_hex("#FFFFFF") == "FFFFFF"
    assert clean_hex("FFF") == "FFFFFF"
    assert clean_hex("000") == "000000"
    
    with pytest.raises(ValueError):
        clean_hex("ZZZ")
        
    with pytest.raises(ValueError):
        clean_hex("12345")

def test_hex_to_rgb():
    assert hex_to_rgb("#FF0000") == {"r": 255, "g": 0, "b": 0}
    assert hex_to_rgb("00FF00") == {"r": 0, "g": 255, "b": 0}
    assert hex_to_rgb("000") == {"r": 0, "g": 0, "b": 0}

def test_hex_to_hsl():
    assert hex_to_hsl("#FF0000") == {"h": 0, "s": 100, "l": 50}
    assert hex_to_hsl("00FF00") == {"h": 120, "s": 100, "l": 50}
    assert hex_to_hsl("0000FF") == {"h": 240, "s": 100, "l": 50}
    assert hex_to_hsl("FFFFFF") == {"h": 0, "s": 0, "l": 100}
    assert hex_to_hsl("000000") == {"h": 0, "s": 0, "l": 0}
