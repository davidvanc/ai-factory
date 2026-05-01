def is_palindrome(s: str) -> bool:
    """Return True if s is a palindrome, ignoring case, spaces, and punctuation."""
    filtered = ''.join(ch for ch in s if ch.isalpha()).lower()
    return filtered == filtered[::-1]
