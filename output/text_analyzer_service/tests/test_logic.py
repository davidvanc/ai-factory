from src.logic import count_letters, count_words, count_vowels, is_palindrome, analyze_text

def test_count_vowels_upper_and_lower():
    assert count_vowels("aAeEiIoOuU") == 10
    assert count_vowels("hAllO") == 2
    assert count_vowels("xyz") == 0

def test_is_palindrome_ignores_spaces_and_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("Was it a car or a cat I saw?") is True
    assert is_palindrome("No lemon, no melon") is True
    assert is_palindrome("Not a palindrome") is False

def test_analyze_text_empty():
    result = analyze_text("")
    assert result["letter_count"] == 0
    assert result["word_count"] == 0
    assert result["vowel_count"] == 0
    assert result["is_palindrome"] is True
