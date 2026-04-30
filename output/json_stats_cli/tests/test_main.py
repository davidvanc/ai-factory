import pytest
from click.testing import CliRunner
from src.main import main
import json
import os

def test_cli_juiste_output():
    runner = CliRunner()
    data = [1,2,3,4,5]
    filepath = 'test_cli_temp.json'
    with open(filepath, 'w') as f:
        json.dump(data, f)
    try:
        result = runner.invoke(main, [filepath])
        assert result.exit_code == 0
        assert "Som: 15" in result.output
        assert "Gemiddelde: 3.0" in result.output
        assert "Maximum: 5" in result.output
    finally:
        os.remove(filepath)

def test_cli_ontbrekend_argument():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output

def test_cli_niet_bestaand_bestand():
    runner = CliRunner()
    result = runner.invoke(main, ['niet_bestaand.json'])
    assert result.exit_code == 1
    assert "Fout" in result.output

def test_cli_ongeldig_json():
    runner = CliRunner()
    filepath = 'test_cli_invalid.json'
    with open(filepath, 'w') as f:
        f.write("geen json")
    try:
        result = runner.invoke(main, [filepath])
        assert result.exit_code == 1
        assert "Fout" in result.output
    finally:
        os.remove(filepath)
