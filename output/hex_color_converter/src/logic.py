def hex_to_rgb(hex_str: str) -> dict:
    hex_str = hex_str.lstrip('#')
    return {
        "r": int(hex_str[0:2], 16),
        "g": int(hex_str[2:4], 16),
        "b": int(hex_str[4:6], 16)
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
        h = 0.0
        s = 0.0
    else:
        if cmax == r:
            h = ((g - b) / delta) % 6
        elif cmax == g:
            h = ((b - r) / delta) + 2
        else:
            h = ((r - g) / delta) + 4
        
        h = h * 60
        s = delta / (1 - abs(2 * l - 1))
        
    return {
        "h": round(h),
        "s": round(s * 100),
        "l": round(l * 100)
    }
