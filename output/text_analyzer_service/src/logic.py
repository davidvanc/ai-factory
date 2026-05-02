import re

def count_letters(text: str) -> int:
    return sum(1 for char in text if char.isalpha())

def count_words(text: str) -> int:
    return len(text.split()) if text.strip() else 0

def count_vowels(text: str) -> int:
    vowels = set("aeiouAEIOU")
    return sum(1 for char in text if char in vowels)

def is_palindrome(text: str) -> bool:
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    if not cleaned:
        return True
    return cleaned == cleaned[::-1]

def analyze_text(text: str) -> dict:
    return {
        "text": text,
        "letter_count": count_letters(text),
        "word_count": count_words(text),
        "vowel_count": count_vowels(text),
        "is_palindrome": is_palindrome(text)
    }
