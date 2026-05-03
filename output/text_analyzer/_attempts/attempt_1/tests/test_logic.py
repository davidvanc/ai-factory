from src.logic import analyze_text

def test_analyze_text_basic():
    result = analyze_text("Racecar is snel")
    assert result["text"] == "Racecar is snel"
    assert result["letter_count"] == 13
    assert result["word_count"] == 3
    assert result["vowel_count"] == 5
    assert result["is_palindrome"] is False

def test_analyze_text_palindrome_lepel():
    result = analyze_text("lepel")
    assert result["is_palindrome"] is True

def test_analyze_text_palindrome_race_car():
    result = analyze_text("Race car")
    assert result["is_palindrome"] is True

def test_analyze_text_no_letters():
    result = analyze_text("123 456")
    assert result["letter_count"] == 0
    assert result["word_count"] == 2
    assert result["vowel_count"] == 0
    assert result["is_palindrome"] is False
