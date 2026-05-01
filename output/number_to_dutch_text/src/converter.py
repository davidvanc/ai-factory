from decimal import Decimal, InvalidOperation

_ONES = {
    0: 'nul', 1: 'een', 2: 'twee', 3: 'drie', 4: 'vier',
    5: 'vijf', 6: 'zes', 7: 'zeven', 8: 'acht', 9: 'negen',
    10: 'tien', 11: 'elf', 12: 'twaalf', 13: 'dertien',
    14: 'veertien', 15: 'vijftien', 16: 'zestien',
    17: 'zeventien', 18: 'achttien', 19: 'negentien'
}
_TENS = {
    20: 'twintig', 30: 'dertig', 40: 'veertig', 50: 'vijftig',
    60: 'zestig', 70: 'zeventig', 80: 'tachtig', 90: 'negentig'
}


def _int_under_100(n: int) -> str:
    """Convert 0-99 to Dutch text (0 returns empty string)."""
    if n == 0:
        return ''
    if n < 20:
        return _ONES[n]
    tens = (n // 10) * 10
    ones = n % 10
    tens_word = _TENS[tens]
    if ones == 0:
        return tens_word
    ones_word = _ONES[ones]
    return f"{ones_word}en{tens_word}"


def _int_under_1000(n: int) -> str:
    """Convert 0-999 to Dutch text (0 returns empty string)."""
    if n == 0:
        return ''
    if n < 100:
        return _int_under_100(n)
    hundreds = n // 100
    remainder = n % 100
    # 100 is just 'honderd', 200 is 'tweehonderd', etc.
    if hundreds == 1:
        hundreds_word = 'honderd'
    else:
        hundreds_word = _ONES[hundreds] + 'honderd'
    if remainder == 0:
        return hundreds_word
    return hundreds_word + _int_under_100(remainder)


def _integer_to_dutch(n: int) -> str:
    """Convert integer 0-999,999,999 to Dutch text."""
    if n == 0:
        return 'nul'
    if n == 1:
        return 'één'

    millions = n // 1_000_000
    thousands = (n % 1_000_000) // 1_000
    hundreds = n % 1_000

    parts = []

    if millions > 0:
        if millions == 1:
            parts.append('één miljoen')
        else:
            parts.append(_int_under_1000(millions) + ' miljoen')

    if thousands > 0:
        if thousands == 1:
            parts.append('duizend')
        else:
            parts.append(_int_under_1000(thousands) + ' duizend')

    if hundreds > 0:
        part = _int_under_1000(hundreds)
        parts.append(part)

    # Insert 'en' before the last part if it is a small number (<100) and there is a previous part
    if len(parts) > 1 and hundreds > 0 and hundreds < 100:
        small = parts[-1]
        if small == 'een':
            small = 'één'
        parts[-1] = 'en ' + small

    return ' '.join(parts)


def _decimal_to_dutch(dec_str: str) -> str:
    """Convert decimal string (up to 2 digits) to Dutch text."""
    if not dec_str:
        return ''
    num = int(dec_str)
    if num == 0:
        return 'nul'
    return _integer_to_dutch(num)


def convert_number_to_dutch_text(number) -> str:
    """
    Convert a number (int, float, Decimal, string) to Dutch text.
    Supports numbers from 0 up to 999,999,999.99.
    Raises ValueError for invalid or out-of-range numbers.
    """
    if isinstance(number, (int, float)):
        number = str(number)
    if isinstance(number, str):
        number = number.replace(',', '.')
    try:
        dec = Decimal(number)
    except InvalidOperation:
        raise ValueError("Ongeldig getal")

    if dec < 0:
        raise ValueError("Negatieve getallen zijn niet toegestaan")
    if dec > Decimal('999999999.99'):
        raise ValueError("Getal is te groot (maximum 999.999.999,99)")

    # Split integer and decimal parts
    if dec == dec.to_integral_value():
        # No fractional part
        integer_part = int(dec)
        decimal_str = ''
    else:
        str_val = str(dec)
        if '.' in str_val:
            int_str, frac_str = str_val.split('.')
        else:
            int_str, frac_str = str_val, ''
        # Truncate to 2 decimal places
        frac_str = (frac_str + '00')[:2]
        integer_part = int(int_str)
        decimal_str = frac_str

    integer_text = _integer_to_dutch(integer_part)
    if decimal_str:
        decimal_text = _decimal_to_dutch(decimal_str)
        return f"{integer_text} komma {decimal_text}"
    return integer_text
