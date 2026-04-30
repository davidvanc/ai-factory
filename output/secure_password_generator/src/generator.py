import random
import string

_system_random = random.SystemRandom()

def generate_password(length: int = 16, use_special: bool = True) -> str:
    """
    Generate a cryptographically secure random password.

    Args:
        length: Desired password length (default 16).
        use_special: Whether to include special characters (default True).

    Returns:
        A random password string.
    """
    letters = string.ascii_letters
    digits = string.digits
    special = string.punctuation if use_special else ''
    pool = letters + digits + special

    if not pool:
        raise ValueError('No characters available for password generation')

    # Ensure at least one letter and one digit are present
    password_chars = []
    password_chars.append(_system_random.choice(letters))
    password_chars.append(_system_random.choice(digits))
    if use_special:
        password_chars.append(_system_random.choice(special))

    remaining_length = length - len(password_chars)
    if remaining_length > 0:
        password_chars.extend(_system_random.choices(pool, k=remaining_length))

    # Shuffle to avoid predictable positions
    _system_random.shuffle(password_chars)

    password = ''.join(password_chars)
    return password
