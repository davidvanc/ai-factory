from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_convert_decimal():
    response = client.post("/convert", json={"value": "23,42"})
    assert response.status_code == 200
    assert response.json() == {"value": "23,42", "text": "drieëntwintig komma tweeënveertig"}

def test_post_convert_trema():
    response = client.post("/convert", json={"value": "82"})
    assert response.status_code == 200
    assert response.json() == {"value": "82", "text": "tweeëntachtig"}

def test_post_convert_basic():
    response1 = client.post("/convert", json={"value": "3"})
    assert response1.json() == {"value": "3", "text": "drie"}

    response2 = client.post("/convert", json={"value": "23"})
    assert response2.json() == {"value": "23", "text": "drieëntwintig"}

def test_post_convert_negative():
    response = client.post("/convert", json={"value": "-5"})
    assert response.json() == {"value": "-5", "text": "min vijf"}

def test_post_convert_zero():
    response = client.post("/convert", json={"value": "0"})
    assert response.json() == {"value": "0", "text": "nul"}

def test_post_convert_biljard():
    response = client.post("/convert", json={"value": "1000000000000000"})
    assert response.json() == {"value": "1000000000000000", "text": "een biljard"}

def test_post_convert_invalid():
    response = client.post("/convert", json={"value": "abc"})
    assert response.status_code in [400, 422]

def test_get_convert():
    response = client.get("/convert?value=-82")
    assert response.status_code == 200
    assert response.json() == {"value": "-82", "text": "min tweeëntachtig"}

def test_get_convert_no_args():
    response = client.get("/convert")
    assert response.status_code == 200
    assert response.json() == {"value": "0", "text": "nul"}

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
