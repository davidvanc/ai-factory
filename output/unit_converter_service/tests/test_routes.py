import pytest

def test_convert_length_meters_to_feet(client):
    response = client.post("/convert/length", json={"value": 100, "from_unit": "meters", "to_unit": "feet"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "meters"
    assert data["to_unit"] == "feet"
    assert abs(data["result"] - 328.084) < 0.1

def test_convert_length_kilometers_to_miles(client):
    response = client.post("/convert/length", json={"value": 5, "from_unit": "kilometers", "to_unit": "miles"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "kilometers"
    assert data["to_unit"] == "miles"
    assert abs(data["result"] - 3.10686) < 0.1

def test_convert_weight_kg_to_lb(client):
    response = client.post("/convert/weight", json={"value": 10, "from_unit": "kg", "to_unit": "lb"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "kg"
    assert data["to_unit"] == "lb"
    assert abs(data["result"] - 22.0462) < 0.1

def test_convert_weight_g_to_oz(client):
    response = client.post("/convert/weight", json={"value": 100, "from_unit": "g", "to_unit": "oz"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "g"
    assert data["to_unit"] == "oz"
    assert abs(data["result"] - 3.5274) < 0.1

def test_convert_temperature_celsius_to_fahrenheit(client):
    response = client.post("/convert/temperature", json={"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "celsius"
    assert data["to_unit"] == "fahrenheit"
    assert abs(data["result"] - 212.0) < 0.1

def test_convert_temperature_kelvin_to_celsius(client):
    response = client.post("/convert/temperature", json={"value": 300, "from_unit": "kelvin", "to_unit": "celsius"})
    assert response.status_code == 200
    data = response.json()
    assert data["from_unit"] == "kelvin"
    assert data["to_unit"] == "celsius"
    assert abs(data["result"] - 26.85) < 0.1

def test_unknown_from_unit_returns_422(client):
    response = client.post("/convert/length", json={"value": 100, "from_unit": "unknown", "to_unit": "feet"})
    assert response.status_code == 422

def test_unknown_to_unit_returns_422(client):
    response = client.post("/convert/weight", json={"value": 100, "from_unit": "kg", "to_unit": "unknown"})
    assert response.status_code == 422

def test_same_from_and_to_unit_returns_same_value(client):
    response = client.post("/convert/temperature", json={"value": 42.5, "from_unit": "celsius", "to_unit": "celsius"})
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == 42.5

def test_logic_convert_length():
    from src.logic import convert_length
    assert abs(convert_length(1, "meters", "feet") - 3.28084) < 0.01

def test_logic_convert_weight():
    from src.logic import convert_weight
    assert abs(convert_weight(1, "kg", "lb") - 2.20462) < 0.01

def test_logic_convert_temperature():
    from src.logic import convert_temperature
    assert abs(convert_temperature(0, "celsius", "fahrenheit") - 32.0) < 0.01

def test_logic_invalid_unit():
    from src.logic import convert_length
    with pytest.raises(ValueError):
        convert_length(1, "meters", "invalid")
