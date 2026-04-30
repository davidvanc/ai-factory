# src/morse.py
# Morse code mapping
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
    '$': '...-..-', '@': '.--.-.', ' ': '/'
}

# Inverse mapping for decoding
MORSE_TO_TEXT = {v: k for k, v in MORSE_CODE_DICT.items()}

def text_to_morse(text: str) -> str:
    """Convert plain text to Morse code."""
    words = text.upper().split()
    morse_words = []
    for word in words:
        morse_chars = []
        for char in word:
            if char in MORSE_CODE_DICT:
                morse_chars.append(MORSE_CODE_DICT[char])
            else:
                morse_chars.append('?')  # unknown character
        morse_words.append(' '.join(morse_chars))
    return ' / '.join(morse_words)

def morse_to_text(morse: str) -> str:
    """Convert Morse code back to plain text."""
    words = morse.strip().split(' / ')
    text_words = []
    for word in words:
        chars = word.split()
        decoded = []
        for code in chars:
            if code in MORSE_TO_TEXT:
                decoded.append(MORSE_TO_TEXT[code])
            else:
                decoded.append('?')  # unknown Morse sequence
        text_words.append(''.join(decoded))
    return ' '.join(text_words)
