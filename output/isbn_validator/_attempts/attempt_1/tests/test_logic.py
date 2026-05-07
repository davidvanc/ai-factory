from src.logic import normalize_isbn, validate_isbn10, validate_isbn13, check_isbn

def test_normalize_isbn():
    assert normalize_isbn("978-3-16-148410-0") == "9783161484100"
    assert normalize_isbn("0 306 40615 2") == "0306406152"
    assert normalize_isbn("12345") == "12345"

def test_validate_isbn10_correct():
    assert validate_isbn10("0306406152") is True
    assert validate_isbn10("080442957X") is True
    assert validate_isbn10("080442957x") is True

def test_validate_isbn10_incorrect():
    assert validate_isbn10("0306406153") is False
    assert validate_isbn10("080442957Y") is False
    assert validate_isbn10("123") is False
    assert validate_isbn10("03064061520") is False

def test_validate_isbn13_correct():
    assert validate_isbn13("9783161484100") is True

def test_validate_isbn13_incorrect():
    assert validate_isbn13("9783161484101") is False
    assert validate_isbn13("123") is False
    assert validate_isbn13("97831614841000") is False
    assert validate_isbn13("978316148410X") is False

def test_check_isbn():
    res = check_isbn("978-3-16-148410-0")
    assert res["valid"] is True
    assert res["format"] == "ISBN-13"
    assert res["normalized"] == "9783161484100"
    assert res["input"] == "978-3-16-148410-0"
    
    res2 = check_isbn("0-306-40615-2")
    assert res2["valid"] is True
    assert res2["format"] == "ISBN-10"
    
    res3 = check_isbn("invalid")
    assert res3["valid"] is False
    assert res3["format"] is None
    
    res4 = check_isbn("")
    assert res4["valid"] is False
    assert res4["format"] is None
