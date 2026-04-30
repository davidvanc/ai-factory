import pytest
from src.validator import validate_hex

def test_valid_hex_6_chars():
    result = validate_hex('FF5733')
    assert result == 'FF5733'

def test_valid_hex_with_hash():
    result = validate_hex('#FF5733')
    assert result == 'FF5733'

def test_valid_hex_3_chars():
    result = validate_hex('FFF')
    assert result == 'FFF'

def test_valid_hex_3_chars_with_hash():
    result = validate_hex('#FFF')
    assert result == 'FFF'

def test_valid_hex_lowercase():
    result = validate_hex('ff5733')
    assert result == 'FF5733'

def test_invalid_hex_too_short():
    with pytest.raises(ValueError):
        validate_hex('FF')

def test_invalid_hex_too_long():
    with pytest.raises(ValueError):
        validate_hex('FF57331')

def test_invalid_hex_non_hex_chars():
    with pytest.raises(ValueError):
        validate_hex('GGGGGG')

def test_invalid_hex_empty_string():
    with pytest.raises(ValueError):
        validate_hex('')

def test_invalid_hex_non_string():
    with pytest.raises(ValueError):
        validate_hex(123456)
