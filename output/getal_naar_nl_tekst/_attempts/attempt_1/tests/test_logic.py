import pytest
from src.logic import number_to_nl_text, int_to_nl

def test_int_to_nl_basic():
    assert int_to_nl(0) == "nul"
    assert int_to_nl(3) == "drie"
    assert int_to_nl(21) == "eenentwintig"
    assert int_to_nl(22) == "tweeëntwintig"
    assert int_to_nl(28) == "achtentwintig"
    assert int_to_nl(82) == "tweeëntachtig"

def test_number_to_nl_text_decimals():
    assert number_to_nl_text("23,42") == "drieëntwintig komma tweeënveertig"
    assert number_to_nl_text("0,05") == "nul komma nul vijf"
    assert number_to_nl_text("0.007") == "nul komma nul nul zeven"

def test_number_to_nl_text_negative():
    assert number_to_nl_text("-5") == "min vijf"
    assert number_to_nl_text("-82") == "min tweeëntachtig"

def test_number_to_nl_text_large():
    assert number_to_nl_text("1000000000000000") == "een biljard"

def test_invalid_input():
    with pytest.raises(ValueError):
        number_to_nl_text("abc")
