from src.logic import validate_email

def test_valid_email():
    valid, reason = validate_email("john.doe@example.com")
    assert valid is True
    assert reason == "valid email address"

def test_consecutive_dots():
    valid, reason = validate_email("john..doe@example.com")
    assert valid is False
    assert "consecutive dots" in reason.lower()

def test_no_tld():
    valid, reason = validate_email("user@localhost")
    assert valid is False
    assert "tld" in reason.lower()

def test_invalid_characters():
    valid, reason = validate_email("user!#@exa mple.com")
    assert valid is False
    assert "invalid characters" in reason.lower()

def test_no_at_symbol():
    valid, reason = validate_email("johndoeexample.com")
    assert valid is False
    assert "@ symbol" in reason.lower()

def test_empty_string():
    valid, reason = validate_email("")
    assert valid is False
    assert "empty" in reason.lower()

def test_edge_cases():
    valid, reason = validate_email(".john@example.com")
    assert valid is False
    assert "start or end with a dot" in reason.lower()
    
    valid, reason = validate_email("john@example.com.")
    assert valid is False
    assert "start or end with a dot" in reason.lower()
    
    valid, reason = validate_email("john@example.123")
    assert valid is False
    assert "invalid tld" in reason.lower()
    
    valid, reason = validate_email("a" * 65 + "@example.com")
    assert valid is False
    assert "exceeds 64 characters" in reason.lower()
    
    valid, reason = validate_email("john@" + "a" * 252 + ".com")
    assert valid is False
    assert "exceeds 255 characters" in reason.lower()

    valid, reason = validate_email("@example.com")
    assert valid is False
    assert "local part cannot be empty" in reason.lower()

    valid, reason = validate_email("john@")
    assert valid is False
    assert "domain part cannot be empty" in reason.lower()

    valid, reason = validate_email("user!#$%&'*+-/=?^_`{|}~@example.com")
    assert valid is True
