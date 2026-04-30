import re

def validate_hex(hex_color: str) -> str:
    """Validate and normalize a hex color code. Returns hex without #."""
    if not isinstance(hex_color, str):
        raise ValueError("Input must be a string")

    hex_color = hex_color.strip()

    # Remove # prefix if present
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    # Check length
    if len(hex_color) not in (3, 6):
        raise ValueError(f"Invalid hex color: {hex_color}. Must be 3 or 6 characters.")

    # Check valid hex characters
    if not re.match(r'^[0-9a-fA-F]+$', hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}. Contains non-hex characters.")

    return hex_color.upper()