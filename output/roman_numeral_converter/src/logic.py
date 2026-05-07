def int_to_roman(num: int) -> str:
    if not isinstance(num, int) or not (1 <= num <= 3999):
        raise ValueError("Number must be an integer between 1 and 3999")
        
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def roman_to_int(roman: str) -> int:
    if not roman:
        raise ValueError("Empty string")
    
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    
    if any(c not in roman_values for c in roman):
        raise ValueError("Invalid characters")
        
    total = 0
    prev_value = 0
    
    for char in reversed(roman):
        value = roman_values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
        
    if int_to_roman(total) != roman:
        raise ValueError("Not a canonical Roman numeral")
        
    return total
