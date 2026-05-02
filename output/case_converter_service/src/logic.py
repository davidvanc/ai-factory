import re

SUPPORTED_CASES = ["upper", "lower", "title", "snake", "kebab", "camel"]

def get_words(text: str) -> list[str]:
    if not text:
        return []
    # Insert space before capital letters if preceded by lowercase (handles camelCase)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Replace all non-alphanumeric characters with space
    text = re.sub(r'[^a-zA-Z0-9]', ' ', text)
    return [word for word in text.split() if word]

def to_upper(text: str) -> str:
    return " ".join(w.upper() for w in get_words(text))

def to_lower(text: str) -> str:
    return " ".join(w.lower() for w in get_words(text))

def to_title(text: str) -> str:
    return " ".join(w.capitalize() for w in get_words(text))

def to_snake(text: str) -> str:
    return "_".join(w.lower() for w in get_words(text))

def to_kebab(text: str) -> str:
    return "-".join(w.lower() for w in get_words(text))

def to_camel(text: str) -> str:
    words = get_words(text)
    if not words:
        return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])

def convert_case(text: str, target_case: str) -> str:
    if target_case == "upper":
        return to_upper(text)
    elif target_case == "lower":
        return to_lower(text)
    elif target_case == "title":
        return to_title(text)
    elif target_case == "snake":
        return to_snake(text)
    elif target_case == "kebab":
        return to_kebab(text)
    elif target_case == "camel":
        return to_camel(text)
    else:
        raise ValueError(f"Unsupported case: {target_case}")
