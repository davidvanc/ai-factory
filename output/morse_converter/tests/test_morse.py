# tests/test_morse.py
import pytest
from click.testing import CliRunner
from src.morse import text_to_morse, morse_to_text
from src.main import cli

def test_text_to_morse_conversion():
    assert text_to_morse("HELLO WORLD") == ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
    assert text_to_morse("SOS") == "... --- ..."

def test_morse_to_text_conversion():
    assert morse_to_text(".... . .-.. .-.. --- / .-- --- .-. .-.. -..") == "HELLO WORLD"
    assert morse_to_text("... --- ...") == "SOS"

def test_case_insensitivity():
    upper = text_to_morse("Hello")
    lower = text_to_morse("hello")
    assert upper == lower

def test_unknown_characters():
    # unknown character should become '?' in Morse
    assert text_to_morse("HELLO? WORLD!") == ".... . .-.. .-.. --- ..--.. / .-- --- .-. .-.. -.. -.-.--"
    # unknown Morse sequence should become '?' in text
    assert morse_to_text(".-.-.-") == "?"

def test_cli_arguments():
    runner = CliRunner()
    # test encode
    result = runner.invoke(cli, ["encode", "SOS"])
    assert result.exit_code == 0
    assert result.output.strip() == "... --- ..."
    # test decode
    result = runner.invoke(cli, ["decode", "... --- ..."])
    assert result.exit_code == 0
    assert result.output.strip() == "SOS"
    # test no args
    result = runner.invoke(cli, [])
    assert result.exit_code != 0  # should show help or error