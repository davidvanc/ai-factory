import regex

def reverse_string(text: str) -> str:
    """
    Reverses a string by individual code points.
    This is the standard Python string reversal.
    """
    return text[::-1]

def reverse_graphemes(text: str) -> str:
    """
    Reverses a string by Unicode grapheme clusters.
    This ensures that compound emojis and combining diacritical marks remain intact.
    """
    if not text:
        return ""
    # \X matches an extended Unicode sequence (grapheme cluster)
    graphemes = regex.findall(r'\X', text)
    return "".join(graphemes[::-1])

def perform_reverse(text: str, unicode_safe: bool) -> str:
    """
    Helper function to reverse a string based on the unicode_safe flag.
    """
    if unicode_safe:
        return reverse_graphemes(text)
    return reverse_string(text)
