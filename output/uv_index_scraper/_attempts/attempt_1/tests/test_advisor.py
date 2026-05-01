from unittest.mock import patch
from src.advisor import get_advice
from src.main import main

def test_advice_low_uv2():
    advice = get_advice(2)
    assert "Laag" in advice
    assert "minimale bescherming" in advice.lower()

def test_advice_moderate_uv5():
    advice = get_advice(5)
    assert "Gemiddeld" in advice
    assert "zonnecrème" in advice.lower()

def test_advice_very_high_uv8():
    advice = get_advice(8)
    assert "Zeer hoog" in advice
    assert "schaduw" in advice.lower()

def test_advice_extreme_uv11():
    advice = get_advice(11)
    assert "Extreem" in advice
    assert "maximale bescherming" in advice.lower()

def test_main_function_prints_correctly(capsys):
    with patch('src.main.fetch_uv_index', return_value=5):
        main()
        captured = capsys.readouterr()
        assert "UV-index 5" in captured.out
        assert "Gemiddeld" in captured.out
        assert "zonnecrème" in captured.out