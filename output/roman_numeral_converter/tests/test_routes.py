import pytest

def test_to_roman_1(client):
    response = client.post("/to-roman", json={"number": 1})
    assert response.status_code == 200
    assert response.json()["roman"] == "I"

def test_to_roman_4(client):
    response = client.post("/to-roman", json={"number": 4})
    assert response.status_code == 200
    assert response.json()["roman"] == "IV"

def test_to_roman_9(client):
    response = client.post("/to-roman", json={"number": 9})
    assert response.status_code == 200
    assert response.json()["roman"] == "IX"

def test_to_roman_1994(client):
    response = client.post("/to-roman", json={"number": 1994})
    assert response.status_code == 200
    assert response.json()["roman"] == "MCMXCIV"

def test_to_roman_3999(client):
    response = client.post("/to-roman", json={"number": 3999})
    assert response.status_code == 200
    assert response.json()["roman"] == "MMMCMXCIX"

def test_to_roman_0(client):
    response = client.post("/to-roman", json={"number": 0})
    assert response.status_code == 422

def test_to_roman_4000(client):
    response = client.post("/to-roman", json={"number": 4000})
    assert response.status_code == 422

def test_to_roman_negative(client):
    response = client.post("/to-roman", json={"number": -1})
    assert response.status_code == 422

def test_to_integer_iv(client):
    response = client.post("/to-integer", json={"roman": "IV"})
    assert response.status_code == 200
    assert response.json()["number"] == 4

def test_to_integer_mcmxciv(client):
    response = client.post("/to-integer", json={"roman": "MCMXCIV"})
    assert response.status_code == 200
    assert response.json()["number"] == 1994

def test_to_integer_iiii(client):
    response = client.post("/to-integer", json={"roman": "IIII"})
    assert response.status_code == 422

def test_to_integer_viiii(client):
    response = client.post("/to-integer", json={"roman": "VIIII"})
    assert response.status_code == 422

def test_to_integer_empty(client):
    response = client.post("/to-integer", json={"roman": ""})
    assert response.status_code == 422

def test_to_integer_invalid_chars(client):
    response = client.post("/to-integer", json={"roman": "ABC"})
    assert response.status_code == 422

def test_convert_to_roman(client):
    response = client.get("/convert?value=42")
    assert response.status_code == 200
    assert response.json()["output"] == "XLII"
    assert response.json()["output_type"] == "roman"

def test_convert_to_integer(client):
    response = client.get("/convert?value=XLII")
    assert response.status_code == 200
    assert response.json()["output"] == 42
    assert response.json()["output_type"] == "integer"

def test_convert_invalid(client):
    response = client.get("/convert?value=0")
    assert response.status_code == 422
    response = client.get("/convert?value=IIII")
    assert response.status_code == 422

def test_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
