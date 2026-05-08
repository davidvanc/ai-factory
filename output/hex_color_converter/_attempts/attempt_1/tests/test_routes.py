def test_to_rgb_with_leading_hash(client):
    response = client.post("/to-rgb", json={"hex": "#FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_rgb_without_leading_hash(client):
    response = client.post("/to-rgb", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_hsl_valid_hex(client):
    response = client.post("/to-hsl", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"hsl": {"h": 11, "s": 100, "l": 60}}

def test_convert_returns_both_rgb_and_hsl(client):
    response = client.get("/convert?hex=FF5733")
    assert response.status_code == 200
    data = response.json()
    assert data["hex"] == "FF5733"
    assert data["rgb"] == {"r": 255, "g": 87, "b": 51}
    assert data["hsl"] == {"h": 11, "s": 100, "l": 60}

def test_invalid_hex_input_returns_error(client):
    response = client.post("/to-rgb", json={"hex": "invalid"})
    assert response.status_code == 422
    
    response = client.post("/to-hsl", json={"hex": "12345"})
    assert response.status_code == 422

    response = client.get("/convert?hex=ZZZ")
    assert response.status_code == 422

def test_short_hex_codes_handled_correctly(client):
    response = client.post("/to-rgb", json={"hex": "#FFF"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 255, "b": 255}}
    
    response = client.get("/convert?hex=000")
    assert response.status_code == 200
    assert response.json()["rgb"] == {"r": 0, "g": 0, "b": 0}
