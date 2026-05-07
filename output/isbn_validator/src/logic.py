import re

def normalize_isbn(isbn: str) -> str:
    """Removes hyphens and spaces from the ISBN string."""
    return re.sub(r'[\s\-]', '', isbn)

def validate_isbn10(isbn: str) -> bool:
    """Validates an ISBN-10 string (assumes already normalized)."""
    if len(isbn) != 10:
        return False
    if not re.match(r'^\d{9}[\dX]$', isbn, re.IGNORECASE):
        return False
    
    total = 0
    for i in range(9):
        total += int(isbn[i]) * (10 - i)
    
    check_digit = isbn[9].upper()
    if check_digit == 'X':
        total += 10
    else:
        total += int(check_digit)
        
    return total % 11 == 0

def validate_isbn13(isbn: str) -> bool:
    """Validates an ISBN-13 string (assumes already normalized)."""
    if len(isbn) != 13:
        return False
    if not re.match(r'^\d{13}$', isbn):
        return False
        
    total = 0
    for i in range(12):
        weight = 1 if i % 2 == 0 else 3
        total += int(isbn[i]) * weight
        
    check_digit = int(isbn[12])
    return (10 - (total % 10)) % 10 == check_digit

def check_isbn(isbn: str) -> dict:
    """Normalizes and checks if an ISBN is valid, returning details."""
    normalized = normalize_isbn(isbn)
    
    format_type = None
    is_valid = False
    
    if len(normalized) == 10:
        format_type = "ISBN-10"
        is_valid = validate_isbn10(normalized)
    elif len(normalized) == 13:
        format_type = "ISBN-13"
        is_valid = validate_isbn13(normalized)
        
    return {
        "valid": is_valid,
        "format": format_type,
        "normalized": normalized,
        "input": isbn
    }
