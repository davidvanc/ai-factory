def count_letters(text: str) -> int:
    return sum(1 for char in text if char.isalpha())

def count_words(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())

def count_vowels(text: str) -> int:
    vowels = set('aeiouAEIOU')
    return sum(1 for char in text if char in vowels)

def is_palindrome(text: str) -> bool:
    cleaned = ''.join(char.lower() for char in text if char.isalnum())
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
