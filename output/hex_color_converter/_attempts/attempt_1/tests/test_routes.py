from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_convert_correct_output():
    response = client.post("/convert", json={"hex": "#FF5733"})
    assert response.status_code == 200
    data = response.json()
    assert data["hex"] == "#FF5733"
    assert data["rgb"] == {"r": 255, "g": 87, "b": 51}
    assert data["hsl"] == {"h": 10.59, "s": 100.0, "l": 60.0}

def test_post_convert_with_or_without_hash():
    res1 = client.post("/convert", json={"hex": "#FF5733"})
    res2 = client.post("/convert", json={"hex": "FF5733"})
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()

def test_post_convert_case_insensitive():
    res1 = client.post("/convert", json={"hex": "ff5733"})
    res2 = client.post("/convert", json={"hex": "FF5733"})
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()

def test_post_convert_invalid_hex():
    response = client.post("/convert", json={"hex": "invalid_hex"})
    assert response.status_code in [400, 422]

def test_post_convert_missing_hex():
    response = client.post("/convert", json={})
    assert response.status_code == 422

def test_get_convert_correct_output():
    response = client.get("/convert?hex=FF5733")
    assert response.status_code == 200
    data = response.json()
    assert data["hex"] == "#FF5733"
    assert data["rgb"] == {"r": 255, "g": 87, "b": 51}
    assert data["hsl"] == {"h": 10.59, "s": 100.0, "l": 60.0}

def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
