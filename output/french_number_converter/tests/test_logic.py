from src.logic import number_to_french

def test_logic_0():
    assert number_to_french(0) == "z\u00e9ro"

def test_logic_80():
    assert number_to_french(80) == "quatre-vingts"

def test_logic_81():
    assert number_to_french(81) == "quatre-vingt-un"

def test_logic_91():
    assert number_to_french(91) == "quatre-vingt-onze"

def test_logic_70():
    assert number_to_french(70) == "soixante-dix"

def test_logic_71():
    assert number_to_french(71) == "soixante et onze"

def test_logic_100():
    assert number_to_french(100) == "cent"

def test_logic_200():
    assert number_to_french(200) == "deux cents"

def test_logic_201():
    assert number_to_french(201) == "deux cent un"

def test_logic_1000():
    assert number_to_french(1000) == "mille"

def test_logic_1000000():
    assert number_to_french(1000000) == "un million"

def test_logic_2000000():
    assert number_to_french(2000000) == "deux millions"

def test_logic_1000000000():
    assert number_to_french(1000000000) == "un milliard"

def test_logic_1000000000000000():
    assert number_to_french(1000000000000000) == "un billiard"
