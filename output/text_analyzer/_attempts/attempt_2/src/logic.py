def analyze_text(text: str) -> dict:
    # Aantal letters (alleen alfabetische karakters)
    letter_count = sum(1 for char in text if char.isalpha())
    
    # Aantal woorden (gesplitst op whitespace)
    word_count = len(text.split())
    
    # Aantal klinkers (inclusief hoofdletters)
    vowels = set("aeiouAEIOU")
    vowel_count = sum(1 for char in text if char in vowels)
    
    # Palindroom check (negeer spaties, leestekens en case)
    cleaned_text = "".join(char.lower() for char in text if char.isalpha())
    is_palindrome = cleaned_text == cleaned_text[::-1] if cleaned_text else False
    
    return {
        "text": text,
        "letter_count": letter_count,
        "word_count": word_count,
        "vowel_count": vowel_count,
        "is_palindrome": is_palindrome
    }
