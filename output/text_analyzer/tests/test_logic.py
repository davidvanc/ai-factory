from src.logic import count_letters, count_words, count_vowels, is_palindrome, analyze_text

def test_count_letters():
    assert count_letters("Hallo wereld!") == 11
    assert count_letters("") == 0
    assert count_letters("12345") == 0

def test_count_words():
    assert count_words("Hallo wereld") == 2
    assert count_words("  ") == 0
    assert count_words("") == 0
    assert count_words("Een, twee, drie!") == 3

def test_count_vowels():
    assert count_vowels("Hallo wereld") == 4
    assert count_vowels("bcdfg") == 0
    assert count_vowels("AEIOUaeiou") == 10

def test_is_palindrome():
    assert is_palindrome("Lepel") is True
    assert is_palindrome("racecar") is True
    assert is_palindrome("A man a plan a canal Panama") is True
    assert is_palindrome("Hallo") is False
    assert is_palindrome("") is True

def test_analyze_text():
    result = analyze_text("Lepel")
    assert result["text"] == "Lepel"
    assert result["letter_count"] == 5
    assert result["word_count"] == 1
    assert result["vowel_count"] == 2
    assert result["is_palindrome"] is True
