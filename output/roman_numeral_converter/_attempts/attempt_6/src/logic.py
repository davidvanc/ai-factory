ROMAN_NUMERALS = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
]

def int_to_roman(num: int) -> str:
    if not isinstance(num, int) or isinstance(num, bool) or not (1 <= num <= 3999):
        raise ValueError("Number must be an integer between 1 and 3999")
    
    result = []
    for value, symbol in ROMAN_NUMERALS:
        while num >= value:
            result.append(symbol)
            num -= value
    return "".join(result)

def roman_to_int(s: str) -> int:
    if not s or not isinstance(s, str):
        raise ValueError("Input must be a non-empty string")
    
    s = s.upper()
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_value = 0
    
    for char in reversed(s):
        if char not in roman_values:
            raise ValueError(f"Invalid Roman numeral character: {char}")
        value = roman_values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value

    # Validate canonical form by converting back
    if int_to_roman(total) != s:
        raise ValueError("Not a valid canonical Roman numeral")

    return total
