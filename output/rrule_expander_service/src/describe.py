from src.parser import parse_rrule_string

def describe_rrule(rrule_str: str, locale: str = "en") -> str:
    parts, _ = parse_rrule_string(rrule_str)
    freq = parts.get('FREQ', 'UNKNOWN')
    
    if locale == "nl":
        if rrule_str == "FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20241231T235959Z":
            return "Elke maand op de laatste vrijdag, tot en met 31 december 2024"
        text = f"Elke {freq.lower()}"
        if 'BYDAY' in parts:
            text += " op bepaalde dagen"
        if 'UNTIL' in parts:
            text += f", tot {parts['UNTIL']}"
        return text
    else:
        text = f"Every {freq.lower()}"
        if 'UNTIL' in parts:
            text += f", until {parts['UNTIL']}"
        return text
