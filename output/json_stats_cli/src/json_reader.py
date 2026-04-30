import json
import os

def read_json(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Bestand {filepath} niet gevonden")
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ongeldig JSON bestand: {e}")
    if not isinstance(data, list):
        raise ValueError("JSON bestand moet een lijst bevatten")
    if len(data) == 0:
        raise ValueError("Lijst is leeg")
    for i, item in enumerate(data):
        if not isinstance(item, (int, float)):
            raise ValueError(f"Element op index {i} is niet numeriek: {item}")
    return data
