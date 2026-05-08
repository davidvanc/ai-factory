import re

def clean_hex(hex_str: str) -> str:
    hex_str = hex_str.strip()
    if hex_str.startswith('#'):
        hex_str = hex_str[1:]
    
    if len(hex_str) not in (3, 6):
        raise ValueError("Hex string must be 3 or 6 characters long")
        
    if not re.fullmatch(r'[0-9a-fA-F]+', hex_str):
        raise ValueError("Hex string contains invalid characters")
        
    if len(hex_str) == 3:
        hex_str = ''.join(c + c for c in hex_str)
        
    return hex_str.upper()

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    clean = clean_hex(hex_str)
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

def rgb_to_hsl(r: int, g: int, b: int) -> tuple[int, int, int]:
    r_prime = r / 255.0
    g_prime = g / 255.0
    b_prime = b / 255.0
    
    cmax = max(r_prime, g_prime, b_prime)
    cmin = min(r_prime, g_prime, b_prime)
    delta = cmax - cmin
    
    l = (cmax + cmin) / 2.0
    
    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        s = delta / (1.0 - abs(2.0 * l - 1.0))
        if cmax == r_prime:
            h = 60.0 * (((g_prime - b_prime) / delta) % 6.0)
        elif cmax == g_prime:
            h = 60.0 * (((b_prime - r_prime) / delta) + 2.0)
        else:
            h = 60.0 * (((r_prime - g_prime) / delta) + 4.0)
            
    return round(h), round(s * 100), round(l * 100)
