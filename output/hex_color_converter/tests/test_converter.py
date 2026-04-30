from src.converter import hex_to_rgb, hex_to_hsl

def test_hex_ff5733_to_rgb():
    result = hex_to_rgb('FF5733')
    assert result == (255, 87, 51)

def test_hex_ff5733_to_hsl():
    result = hex_to_hsl('FF5733')
    assert result == (11, 100, 60)

def test_hex_with_hash_to_rgb():
    result = hex_to_rgb('#FF5733')
    assert result == (255, 87, 51)

def test_short_hex_to_rgb():
    result = hex_to_rgb('FFF')
    assert result == (255, 255, 255)

def test_short_hex_with_hash_to_rgb():
    result = hex_to_rgb('#FFF')
    assert result == (255, 255, 255)

def test_hex_000000_to_rgb():
    result = hex_to_rgb('000000')
    assert result == (0, 0, 0)

def test_hex_000000_to_hsl():
    result = hex_to_hsl('000000')
    assert result == (0, 0, 0)

def test_hex_ffffff_to_rgb():
    result = hex_to_rgb('FFFFFF')
    assert result == (255, 255, 255)

def test_hex_ffffff_to_hsl():
    result = hex_to_hsl('FFFFFF')
    assert result == (0, 0, 100)
