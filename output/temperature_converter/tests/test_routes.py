def test_celsius_to_fahrenheit_endpoint(client):
    response = client.post("/convert/celsius-to-fahrenheit", json={"value": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == 212.0
    assert data["input_unit"] == "Celsius"
    assert data["output_unit"] == "Fahrenheit"

def test_fahrenheit_to_celsius_endpoint(client):
    response = client.post("/convert/fahrenheit-to-celsius", json={"value": 32.0})
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == 0.0
    assert data["input_unit"] == "Fahrenheit"
    assert data["output_unit"] == "Celsius"

def test_convert_endpoint_c_to_f(client):
    response = client.post("/convert", json={"value": 0.0, "from_unit": "C", "to_unit": "F"})
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == 32.0
    assert data["input_unit"] == "C"
    assert data["output_unit"] == "F"

def test_convert_endpoint_same_unit(client):
    response = client.post("/convert", json={"value": 25.0, "from_unit": "C", "to_unit": "C"})
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == 25.0
    assert data["input_unit"] == "C"
    assert data["output_unit"] == "C"

def test_convert_endpoint_invalid_unit(client):
    response = client.post("/convert", json={"value": 10.0, "from_unit": "K", "to_unit": "C"})
    assert response.status_code in [400, 422]

def test_convert_endpoint_invalid_value_type(client):
    response = client.post("/convert/celsius-to-fahrenheit", json={"value": "not-a-number"})
    assert response.status_code == 422

def test_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "temperature_converter"
