import re

def clean_hex(hex_str: str) -> str:
    hex_str = hex_str.strip().lstrip('#')
    if not re.fullmatch(r'[0-9a-fA-F]+', hex_str):
        raise ValueError("Invalid hex characters")
    if len(hex_str) == 3:
        hex_str = ''.join(c + c for c in hex_str)
    elif len(hex_str) != 6:
        raise ValueError("Hex color must be 3 or 6 characters long")
    return hex_str

def hex_to_rgb(hex_str: str) -> dict:
    clean = clean_hex(hex_str)
    return {
        "r": int(clean[0:2], 16),
        "g": int(clean[2:4], 16),
        "b": int(clean[4:6], 16)
    }

def hex_to_hsl(hex_str: str) -> dict:
    rgb = hex_to_rgb(hex_str)
    r = rgb["r"] / 255.0
    g = rgb["g"] / 255.0
    b = rgb["b"] / 255.0

    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin

    l = (cmax + cmin) / 2.0

    if delta == 0:
        h = 0
        s = 0
    else:
        if l < 0.5:
            s = delta / (cmax + cmin)
        else:
            s = delta / (2.0 - cmax - cmin)

        if cmax == r:
            h = (g - b) / delta
            if g < b:
                h += 6
        elif cmax == g:
            h = (b - r) / delta + 2
        else:
            h = (r - g) / delta + 4
        h *= 60

    return {
        "h": round(h),
        "s": round(s * 100),
        "l": round(l * 100)
    }
