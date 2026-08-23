import pytest
from src.logic import reverse_string, reverse_graphemes, perform_reverse

def test_reverse_string_ascii():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("12345") == "54321"
    assert reverse_string("Hello World!") == "!dlroW olleH"

def test_reverse_string_empty():
    assert reverse_string("") == ""

def test_reverse_graphemes_empty():
    assert reverse_graphemes("") == ""

def test_reverse_graphemes_ascii():
    assert reverse_graphemes("hello") == "olleh"

def test_reverse_graphemes_emoji():
    # Family emoji: Man, Woman, Girl (👨‍👩‍👧)
    # It's a single grapheme cluster.
    emoji = "👨‍👩‍👧"
    assert reverse_graphemes(emoji) == emoji
    
    # Multiple emojis
    emojis = "👨‍👩‍👧🚀🇳🇱"
    assert reverse_graphemes(emojis) == "🇳🇱🚀👨‍👩‍👧"

def test_reverse_string_emoji_corrupts():
    # Reversing by code point will corrupt the compound emoji
    emoji = "👨‍👩‍👧"
    assert reverse_string(emoji) != emoji

def test_reverse_graphemes_diacritics():
    # "cafe" + combining acute accent (U+0301)
    text = "cafe\u0301"
    # Grapheme reverse should keep 'e' and acute accent together
    assert reverse_graphemes(text) == "e\u0301fac"

def test_reverse_string_diacritics_corrupts():
    # "cafe" + combining acute accent (U+0301)
    text = "cafe\u0301"
    # String reverse will put the accent before the 'e'
    assert reverse_string(text) == "\u0301efac"

def test_perform_reverse():
    assert perform_reverse("hello", unicode_safe=False) == "olleh"
    assert perform_reverse("hello", unicode_safe=True) == "olleh"
    
    emoji = "👨‍👩‍👧"
    assert perform_reverse(emoji, unicode_safe=True) == emoji
    assert perform_reverse(emoji, unicode_safe=False) != emoji
    
    assert perform_reverse("", unicode_safe=True) == ""
    assert perform_reverse("", unicode_safe=False) == ""
