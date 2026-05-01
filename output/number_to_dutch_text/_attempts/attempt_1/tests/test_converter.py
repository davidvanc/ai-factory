import pytest
from src.converter import convert_number_to_dutch_text


def test_1():
    assert convert_number_to_dutch_text(1) == 'één'


def test_15():
    assert convert_number_to_dutch_text(15) == 'vijftien'


def test_21():
    assert convert_number_to_dutch_text(21) == 'eenentwintig'


def test_100():
    assert convert_number_to_dutch_text(100) == 'honderd'


def test_1000():
    assert convert_number_to_dutch_text(1000) == 'duizend'


def test_1234567():
    expected = 'één miljoen tweehonderdvierendertig duizend vijfhonderdzevenenzestig'
    assert convert_number_to_dutch_text(1234567) == expected


def test_decimal_1_50():
    assert convert_number_to_dutch_text('1.50') == 'één komma vijftig'


def test_maximum():
    expected = (
        'negenhonderdnegenennegentig miljoen '
        'negenhonderdnegenennegentig duizend '
        'negenhonderdnegenennegentig komma negenennegentig'
    )
    assert convert_number_to_dutch_text('999999999.99') == expected


def test_negative_raises():
    with pytest.raises(ValueError):
        convert_number_to_dutch_text(-1)


def test_too_large_raises():
    with pytest.raises(ValueError):
        convert_number_to_dutch_text('1000000000')
