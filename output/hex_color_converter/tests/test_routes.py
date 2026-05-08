import pytest

def test_to_rgb_with_hash(client):
    response = client.post("/to-rgb", json={"hex": "#FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_rgb_without_hash(client):
    response = client.post("/to-rgb", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"rgb": {"r": 255, "g": 87, "b": 51}}

def test_to_hsl_valid(client):
    response = client.post("/to-hsl", json={"hex": "FF5733"})
    assert response.status_code == 200
    assert response.json() == {"hsl": {"h": 11, "s": 100, "l": 60}}

def test_convert_both(client):
    response = client.get("/convert?hex=FF5733")
    assert response.status_code == 200
    data = response.json()
    assert data["hex"] == "#FF5733"
    assert data["rgb"] == {"r": 255, "g": 87, "b": 51}
    assert data["hsl"] == {"h": 11, "s": 100, "l": 60}

def test_invalid_hex_returns_422(client):
    response = client.post("/to-rgb", json={"hex": "ZZZZZZ"})
    assert response.status_code == 422

def test_too_short_hex_returns_422(client):
    response = client.post("/to-rgb", json={"hex": "FF"})
    assert response.status_code == 422

def test_non_hex_chars_returns_422(client):
    response = client.post("/to-rgb", json={"hex": "#FF573G"})
    assert response.status_code == 422

def test_convert_known_colors(client):
    # Black
    r1 = client.get("/convert?hex=000000")
    assert r1.json()["rgb"] == {"r": 0, "g": 0, "b": 0}
    assert r1.json()["hsl"] == {"h": 0, "s": 0, "l": 0}
    
    # White
    r2 = client.get("/convert?hex=FFFFFF")
    assert r2.json()["rgb"] == {"r": 255, "g": 255, "b": 255}
    assert r2.json()["hsl"] == {"h": 0, "s": 0, "l": 100}
    
    # Red
    r3 = client.get("/convert?hex=FF0000")
    assert r3.json()["rgb"] == {"r": 255, "g": 0, "b": 0}
    assert r3.json()["hsl"] == {"h": 0, "s": 100, "l": 50}
