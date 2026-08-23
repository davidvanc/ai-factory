import pytest

def test_post_reverse_basic(client):
    response = client.post("/reverse", json={"text": "Hallo wereld"})
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == "dlerew ollaH"
    assert data["original"] == "Hallo wereld"
    assert data["length"] == 12

def test_post_reverse_empty_string(client):
    response = client.post("/reverse", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == ""
    assert data["length"] == 0

def test_post_reverse_idempotent(client):
    text = "FastAPI is awesome!"
    res1 = client.post("/reverse", json={"text": text})
    assert res1.status_code == 200
    reversed_text = res1.json()["reversed"]
    
    res2 = client.post("/reverse", json={"text": reversed_text})
    assert res2.status_code == 200
    assert res2.json()["reversed"] == text

def test_post_reverse_unicode_safe_true(client):
    text = "👨‍👩‍👧 cafe\u0301"
    response = client.post("/reverse", json={"text": text, "unicode_safe": True})
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == "e\u0301fac 👨‍👩‍👧"
    assert data["unicode_safe"] is True

def test_post_reverse_unicode_safe_false(client):
    text = "cafe\u0301"
    response = client.post("/reverse", json={"text": text, "unicode_safe": False})
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == "\u0301efac"
    
    res_safe = client.post("/reverse", json={"text": text, "unicode_safe": True})
    assert data["reversed"] != res_safe.json()["reversed"]

def test_post_reverse_missing_text(client):
    response = client.post("/reverse", json={"unicode_safe": True})
    assert response.status_code == 422

def test_post_reverse_invalid_type(client):
    response = client.post("/reverse", json={"text": 12345})
    assert response.status_code == 422

def test_post_reverse_exceeds_max_length(client):
    long_text = "a" * 10001
    response = client.post("/reverse", json={"text": long_text})
    assert response.status_code == 422

def test_post_reverse_batch_success(client):
    items = ["abc", "FastAPI", "🇳🇱"]
    response = client.post("/reverse/batch", json={"items": items, "unicode_safe": True})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["results"]) == 3
    assert data["results"][0]["reversed"] == "cba"
    assert data["results"][1]["reversed"] == "IPAtsaF"
    assert data["results"][2]["reversed"] == "🇳🇱"

def test_post_reverse_batch_exceeds_max_items(client):
    items = ["a"] * 1001
    response = client.post("/reverse/batch", json={"items": items})
    assert response.status_code == 422

def test_post_reverse_batch_empty_list(client):
    response = client.post("/reverse/batch", json={"items": []})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["results"] == []

def test_get_reverse_success(client):
    response = client.get("/reverse?text=microservice")
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == "ecivresorcim"
    assert data["original"] == "microservice"
    assert data["length"] == 12

def test_get_reverse_missing_text(client):
    response = client.get("/reverse")
    assert response.status_code == 422

def test_get_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data

def test_get_reverse_whitespace_newlines(client):
    text = " \n \t hello \n "
    response = client.get("/reverse", params={"text": text})
    assert response.status_code == 200
    data = response.json()
    assert data["reversed"] == " \n olleh \t \n "
    assert data["original"] == text
