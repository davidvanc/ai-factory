import secrets
import string

def generate_password(length: int, include_digits: bool, include_uppercase: bool, include_lowercase: bool, include_symbols: bool) -> str:
    if not any([include_digits, include_uppercase, include_lowercase, include_symbols]):
        raise ValueError("At least one character group must be enabled")
    
    if length < 8 or length > 128:
        raise ValueError("Length must be between 8 and 128")

    pool = ""
    required_chars = []

    if include_digits:
        pool += string.digits
        required_chars.append(secrets.choice(string.digits))
    if include_uppercase:
        pool += string.ascii_uppercase
        required_chars.append(secrets.choice(string.ascii_uppercase))
    if include_lowercase:
        pool += string.ascii_lowercase
        required_chars.append(secrets.choice(string.ascii_lowercase))
    if include_symbols:
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        pool += symbols
        required_chars.append(secrets.choice(symbols))

    remaining_length = length - len(required_chars)
    
    random_chars = [secrets.choice(pool) for _ in range(remaining_length)]
    
    password_list = required_chars + random_chars
    
    secrets.SystemRandom().shuffle(password_list)
    
    return "".join(password_list)
