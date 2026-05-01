"""
Robuuste JSON extractie uit LLM antwoorden.
LLMs leveren soms troep erbij: code fences, extra objecten, uitleg.
Deze utility extracteert het eerste valide JSON object/array.
"""
import json
import re
from typing import Optional, Union


def extract_json(text: str, expect: str = "object") -> Optional[Union[dict, list]]:
    """
    Extracteer het eerste valide JSON object of array uit een tekst.

    Args:
        text: De ruwe LLM output
        expect: "object" voor {...}, "array" voor [...]

    Returns:
        dict / list als parsing slaagt, anders None
    """
    if not text:
        return None

    # Stap 1: code fences strippen
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.replace("```", "")

    # Stap 2: probeer direct te parsen
    text = text.strip()
    try:
        result = json.loads(text)
        if expect == "object" and isinstance(result, dict):
            return result
        if expect == "array" and isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Stap 3: zoek het eerste complete JSON object/array via brace-counting
    open_char = "{" if expect == "object" else "["
    close_char = "}" if expect == "object" else "]"

    start_idx = text.find(open_char)
    if start_idx == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start_idx, len(text)):
        c = text[i]

        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue

        if c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                # Compleet object/array gevonden
                candidate = text[start_idx:i + 1]
                try:
                    result = json.loads(candidate)
                    if expect == "object" and isinstance(result, dict):
                        return result
                    if expect == "array" and isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    # Probeer volgende
                    start_idx = text.find(open_char, i + 1)
                    if start_idx == -1:
                        return None
                    depth = 0
                    continue

    return None
