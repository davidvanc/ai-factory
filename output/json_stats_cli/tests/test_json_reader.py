import pytest
import json
import os
from src.json_reader import read_json

def test_correct_json():
    data = [1, 2, 3, 4, 5]
    filepath = 'test_temp.json'
    with open(filepath, 'w') as f:
        json.dump(data, f)
    try:
        result = read_json(filepath)
        assert result == data
    finally:
        os.remove(filepath)

def test_ongeldig_json():
    filepath = 'test_invalid.json'
    with open(filepath, 'w') as f:
        f.write("dit is geen json")
    try:
        with pytest.raises(ValueError, match="Ongeldig JSON bestand"):
            read_json(filepath)
    finally:
        os.remove(filepath)

def test_niet_bestaand_bestand():
    with pytest.raises(FileNotFoundError):
        read_json('niet_bestaand.json')

def test_lege_lijst():
    filepath = 'test_empty.json'
    with open(filepath, 'w') as f:
        json.dump([], f)
    try:
        with pytest.raises(ValueError, match="Lijst is leeg"):
            read_json(filepath)
    finally:
        os.remove(filepath)

def test_niet_numeriek():
    filepath = 'test_non_numeric.json'
    with open(filepath, 'w') as f:
        json.dump([1, "twee", 3], f)
    try:
        with pytest.raises(ValueError, match="niet numeriek"):
            read_json(filepath)
    finally:
        os.remove(filepath)

def test_sample_data():
    filepath = 'tests/sample_data.json'
    result = read_json(filepath)
    assert result == [1, 2, 3, 4, 5]
