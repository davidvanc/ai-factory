from src.logic import hex_to_rgb, hex_to_hsl

def test_hex_to_rgb():
    assert hex_to_rgb("000000") == {"r": 0, "g": 0, "b": 0}
    assert hex_to_rgb("FFFFFF") == {"r": 255, "g": 255, "b": 255}
    assert hex_to_rgb("FF5733") == {"r": 255, "g": 87, "b": 51}
    assert hex_to_rgb("#FF5733") == {"r": 255, "g": 87, "b": 51}

def test_hex_to_hsl():
    assert hex_to_hsl("000000") == {"h": 0, "s": 0, "l": 0}
    assert hex_to_hsl("FFFFFF") == {"h": 0, "s": 0, "l": 100}
    assert hex_to_hsl("FF5733") == {"h": 11, "s": 100, "l": 60}
    assert hex_to_hsl("#FF5733") == {"h": 11, "s": 100, "l": 60}
