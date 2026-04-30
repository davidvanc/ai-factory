import string
from src.generator import generate_password

def test_default_length():
    pw = generate_password()
    assert len(pw) == 16, f"Expected length 16, got {len(pw)}"

def test_custom_length():
    length = 24
    pw = generate_password(length=length)
    assert len(pw) == length, f"Expected length {length}, got {len(pw)}"

def test_no_special_flag():
    pw = generate_password(use_special=False)
    # Check that no punctuation characters appear
    for ch in pw:
        assert ch not in string.punctuation, f"Found special character: {ch}"

def test_contains_letters_and_digits():
    pw = generate_password()
    has_letter = any(ch in string.ascii_letters for ch in pw)
    has_digit = any(ch in string.digits for ch in pw)
    assert has_letter, "Password must contain at least one letter"
    assert has_digit, "Password must contain at least one digit"

def test_randomness():
    pw1 = generate_password()
    pw2 = generate_password()
    assert pw1 != pw2, "Two generated passwords should not be identical"
