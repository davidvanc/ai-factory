import pytest
import string
from src.logic import generate_password

def test_generate_password_length():
    pwd = generate_password(16, True, True, True, True)
    assert len(pwd) == 16

def test_generate_password_digits_only():
    pwd = generate_password(10, True, False, False, False)
    assert all(c in string.digits for c in pwd)

def test_generate_password_uppercase_only():
    pwd = generate_password(10, False, True, False, False)
    assert all(c in string.ascii_uppercase for c in pwd)

def test_generate_password_lowercase_only():
    pwd = generate_password(10, False, False, True, False)
    assert all(c in string.ascii_lowercase for c in pwd)

def test_generate_password_symbols_only():
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    pwd = generate_password(10, False, False, False, True)
    assert all(c in symbols for c in pwd)

def test_generate_password_invalid_length():
    with pytest.raises(ValueError):
        generate_password(7, True, True, True, True)
    with pytest.raises(ValueError):
        generate_password(129, True, True, True, True)

def test_generate_password_no_groups():
    with pytest.raises(ValueError):
        generate_password(10, False, False, False, False)
