from src.logic import celsius_to_fahrenheit, fahrenheit_to_celsius

def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32.0
    assert celsius_to_fahrenheit(-40) == -40.0
    assert celsius_to_fahrenheit(100) == 212.0

def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(32) == 0.0
    assert fahrenheit_to_celsius(-40) == -40.0
    assert fahrenheit_to_celsius(212) == 100.0
