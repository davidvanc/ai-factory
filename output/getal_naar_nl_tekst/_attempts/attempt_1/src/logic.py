import re

UNITS = ["nul", "een", "twee", "drie", "vier", "vijf", "zes", "zeven", "acht", "negen",
         "tien", "elf", "twaalf", "dertien", "veertien", "vijftien", "zestien", "zeventien", "achttien", "negentien"]

TENS = ["", "", "twintig", "dertig", "veertig", "vijftig", "zestig", "zeventig", "tachtig", "negentig"]

PREFIXES = {
    1: "eenen",
    2: "tweeën",
    3: "drieën",
    4: "vieren",
    5: "vijfen",
    6: "zesen",
    7: "zevenen",
    8: "achten",
    9: "negenen"
}

SCALES = [
    (10**18, "triljoen"),
    (10**15, "biljard"),
    (10**12, "biljoen"),
    (10**9, "miljard"),
    (10**6, "miljoen")
]

def int_to_nl(n: int) -> str:
    if n < 0:
        return "min " + int_to_nl(-n)
    if n < 20:
        return UNITS[n]
    if n < 100:
        tens = n // 10
        units = n % 10
        if units == 0:
            return TENS[tens]
        return PREFIXES[units] + TENS[tens]
    if n < 1000:
        hundreds = n // 100
        remainder = n % 100
        h_str = "honderd" if hundreds == 1 else int_to_nl(hundreds) + "honderd"
        if remainder == 0:
            return h_str
        return h_str + int_to_nl(remainder)
    if n < 1000000:
        thousands = n // 1000
        remainder = n % 1000
        t_str = "duizend" if thousands == 1 else int_to_nl(thousands) + "duizend"
        if remainder == 0:
            return t_str
        return t_str + int_to_nl(remainder)

    for scale, name in SCALES:
        if n >= scale:
            count = n // scale
            remainder = n % scale
            res = int_to_nl(count) + " " + name
            if remainder == 0:
                return res
            return res + " " + int_to_nl(remainder)

    return str(n)

def number_to_nl_text(value_str: str) -> str:
    value_str = value_str.strip()
    if not re.match(r'^-?\d+([.,]\d+)?$', value_str):
        raise ValueError("Invalid number format")

    parts = re.split(r'[.,]', value_str)
    int_part = parts[0]

    if int_part == "-0":
        int_text = "min nul"
    else:
        int_text = int_to_nl(int(int_part))

    if len(parts) == 1:
        return int_text

    dec_part = parts[1]
    if not dec_part:
        return int_text

    leading_zeros = 0
    for char in dec_part:
        if char == '0':
            leading_zeros += 1
        else:
            break

    dec_text_parts = ["nul"] * leading_zeros
    remaining_dec = dec_part[leading_zeros:]

    if remaining_dec:
        dec_text_parts.append(int_to_nl(int(remaining_dec)))

    dec_text = " ".join(dec_text_parts)

    return f"{int_text} komma {dec_text}"
