def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    hex_code = hex_code.lstrip('#')
    if len(hex_code) == 3:
        hex_code = ''.join(c + c for c in hex_code)
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_norm, g_norm, b_norm)
    cmin = min(r_norm, g_norm, b_norm)
    delta = cmax - cmin

    l = (cmax + cmin) / 2.0

    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        s = delta / (1.0 - abs(2.0 * l - 1.0))
        if cmax == r_norm:
            h = 60.0 * (((g_norm - b_norm) / delta) % 6.0)
        elif cmax == g_norm:
            h = 60.0 * (((b_norm - r_norm) / delta) + 2.0)
        else:
            h = 60.0 * (((r_norm - g_norm) / delta) + 4.0)

    h = (h + 360.0) % 360.0

    return round(h, 2), round(s * 100, 2), round(l * 100, 2)

def process_hex_color(hex_code: str) -> dict:
    clean_hex = hex_code.lstrip('#').upper()
    if len(clean_hex) == 3:
        clean_hex = ''.join(c + c for c in clean_hex)
    formatted_hex = f"#{clean_hex}"

    r, g, b = hex_to_rgb(clean_hex)
    h, s, l = rgb_to_hsl(r, g, b)

    return {
        "hex": formatted_hex,
        "rgb": {"r": r, "g": g, "b": b},
        "hsl": {"h": h, "s": s, "l": l}
    }
