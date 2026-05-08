import pytest
from src.logic import clean_hex, hex_to_rgb, rgb_to_hsl

def test_clean_hex():
    assert clean_hex("#FF5733") == "FF5733"
    assert clean_hex("FF5733") == "FF5733"
    assert clean_hex("#F00") == "FF0000"
    assert clean_hex("F00") == "FF0000"
    
    with pytest.raises(ValueError):
        clean_hex("FF")
        
    with pytest.raises(ValueError):
        clean_hex("ZZZZZZ")

def test_hex_to_rgb():
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert hex_to_rgb("#FF0000") == (255, 0, 0)
    assert hex_to_rgb("#FF5733") == (255, 87, 51)

def test_rgb_to_hsl():
    assert rgb_to_hsl(0, 0, 0) == (0, 0, 0)
    assert rgb_to_hsl(255, 255, 255) == (0, 0, 100)
    assert rgb_to_hsl(255, 0, 0) == (0, 100, 50)
    assert rgb_to_hsl(255, 87, 51) == (11, 100, 60)
