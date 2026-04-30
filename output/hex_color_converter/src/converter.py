def hex_to_rgb(hex_color: str) -> tuple:
    """Convert a hex color string (without #) to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)

def hex_to_hsl(hex_color: str) -> tuple:
    """Convert a hex color string (without #) to HSL tuple."""
    r, g, b = hex_to_rgb(hex_color)
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    delta = max_val - min_val

    # Lightness
    l = (max_val + min_val) / 2.0

    # Saturation
    if delta == 0:
        s = 0.0
        h = 0  # integer, not float
    else:
        if l <= 0.5:
            s = delta / (max_val + min_val)
        else:
            s = delta / (2.0 - max_val - min_val)

        # Hue
        if max_val == r_norm:
            h = ((g_norm - b_norm) / delta) % 6
        elif max_val == g_norm:
            h = (b_norm - r_norm) / delta + 2
        else:
            h = (r_norm - g_norm) / delta + 4

        h = round(h * 60)
        if h < 0:
            h += 360

    s = round(s * 100)
    l = round(l * 100)

    return (h, s, l)
