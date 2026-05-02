from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_convert_0():
    response = client.post("/convert", json={"number": 0})
    assert response.status_code == 200
    assert response.json() == {"number": 0, "text": "z\u00e9ro"}

def test_post_convert_80():
    response = client.post("/convert", json={"number": 80})
    assert response.status_code == 200
    assert response.json() == {"number": 80, "text": "quatre-vingts"}

def test_post_convert_81():
    response = client.post("/convert", json={"number": 81})
    assert response.status_code == 200
    assert response.json() == {"number": 81, "text": "quatre-vingt-un"}

def test_post_convert_91():
    response = client.post("/convert", json={"number": 91})
    assert response.status_code == 200
    assert response.json() == {"number": 91, "text": "quatre-vingt-onze"}

def test_post_convert_70():
    response = client.post("/convert", json={"number": 70})
    assert response.status_code == 200
    assert response.json() == {"number": 70, "text": "soixante-dix"}

def test_post_convert_71():
    response = client.post("/convert", json={"number": 71})
    assert response.status_code == 200
    assert response.json() == {"number": 71, "text": "soixante et onze"}

def test_post_convert_100():
    response = client.post("/convert", json={"number": 100})
    assert response.status_code == 200
    assert response.json() == {"number": 100, "text": "cent"}

def test_post_convert_200():
    response = client.post("/convert", json={"number": 200})
    assert response.status_code == 200
    assert response.json() == {"number": 200, "text": "deux cents"}

def test_post_convert_201():
    response = client.post("/convert", json={"number": 201})
    assert response.status_code == 200
    assert response.json() == {"number": 201, "text": "deux cent un"}

def test_post_convert_1000():
    response = client.post("/convert", json={"number": 1000})
    assert response.status_code == 200
    assert response.json() == {"number": 1000, "text": "mille"}

def test_post_convert_1000000():
    response = client.post("/convert", json={"number": 1000000})
    assert response.status_code == 200
    assert response.json() == {"number": 1000000, "text": "un million"}

def test_post_convert_2000000():
    response = client.post("/convert", json={"number": 2000000})
    assert response.status_code == 200
    assert response.json() == {"number": 2000000, "text": "deux millions"}

def test_post_convert_1000000000():
    response = client.post("/convert", json={"number": 1000000000})
    assert response.status_code == 200
    assert response.json() == {"number": 1000000000, "text": "un milliard"}

def test_post_convert_1000000000000000():
    response = client.post("/convert", json={"number": 1000000000000000})
    assert response.status_code == 200
    assert response.json() == {"number": 1000000000000000, "text": "un billiard"}

def test_get_convert_query_param():
    response = client.get("/convert?number=91")
    assert response.status_code == 200
    assert response.json() == {"number": 91, "text": "quatre-vingt-onze"}

def test_negative_numbers_422():
    response = client.post("/convert", json={"number": -1})
    assert response.status_code == 422
    response_get = client.get("/convert?number=-1")
    assert response_get.status_code == 422

def test_numbers_greater_than_1_billiard_422():
    response = client.post("/convert", json={"number": 1000000000000001})
    assert response.status_code == 422
    response_get = client.get("/convert?number=1000000000000001")
    assert response_get.status_code == 422

def test_non_integer_input_422():
    response = client.post("/convert", json={"number": "abc"})
    assert response.status_code == 422
    response_get = client.get("/convert?number=abc")
    assert response_get.status_code == 422

def test_get_status_200():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "range": "0 to 1000000000000000"}

def test_get_health_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
