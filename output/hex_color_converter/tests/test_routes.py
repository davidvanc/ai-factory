def test_to_rgb_with_hash(client):
    response = client.post("/to-rgb", json={"hex": "#FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_rgb_without_hash(client):
    response = client.post("/to-rgb", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_hsl_valid_hex(client):
    response = client.post("/to-hsl", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"hsl": {"h": 11, "s": 100, "l": 60}}

def test_convert_get_both(client):
    response = client.get("/convert?hex=FF5733")
    assert response.status_code == 200
    data = response.json()
    assert data["rgb"] == {"r": 255, "g": 87, "b": 51}
    assert data["hsl"] == {"h": 11, "s": 100, "l": 60}

def test_invalid_hex_input_422(client):
    response = client.post("/to-rgb", json={"hex": "invalid"})
    assert response.status_code == 422

def test_too_short_hex_rejected(client):
    response = client.post("/to-rgb", json={"hex": "#FFF"})
    assert response.status_code == 422

def test_too_long_hex_rejected(client):
    response = client.post("/to-rgb", json={"hex": "#FFFFFF0"})
    assert response.status_code == 422

def test_non_hex_characters_rejected(client):
    response = client.post("/to-rgb", json={"hex": "#ZZZZZZ"})
    assert response.status_code == 422
