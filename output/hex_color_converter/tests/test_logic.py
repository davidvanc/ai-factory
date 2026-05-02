from src.logic import hex_to_rgb, rgb_to_hsl

def test_hex_to_rgb():
    assert hex_to_rgb("FF5733") == (255, 87, 51)
    assert hex_to_rgb("000000") == (0, 0, 0)
    assert hex_to_rgb("FFFFFF") == (255, 255, 255)
    assert hex_to_rgb("F53") == (255, 85, 51)

def test_rgb_to_hsl():
    assert rgb_to_hsl(255, 87, 51) == (10.59, 100.0, 60.0)
    assert rgb_to_hsl(0, 0, 0) == (0.0, 0.0, 0.0)
    assert rgb_to_hsl(255, 255, 255) == (0.0, 0.0, 100.0)
    assert rgb_to_hsl(51, 255, 87) == (130.59, 100.0, 60.0)
