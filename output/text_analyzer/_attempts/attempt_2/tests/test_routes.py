from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_analyze_letter_count():
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["letter_count"] == 13

def test_post_analyze_word_count():
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["word_count"] == 3

def test_post_analyze_vowel_count():
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["vowel_count"] == 5

def test_post_analyze_palindrome_lepel():
    response = client.post("/analyze", json={"text": "lepel"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is True

def test_post_analyze_palindrome_race_car():
    response = client.post("/analyze", json={"text": "Race car"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is True

def test_post_analyze_palindrome_false():
    response = client.post("/analyze", json={"text": "hallo"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is False

def test_get_analyze_query_param():
    response = client.get("/analyze?text=lepel")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "lepel"
    assert data["letter_count"] == 5
    assert data["word_count"] == 1
    assert data["vowel_count"] == 2
    assert data["is_palindrome"] is True

def test_empty_string_422():
    response_post = client.post("/analyze", json={"text": ""})
    assert response_post.status_code == 422
    
    response_get = client.get("/analyze?text=")
    assert response_get.status_code == 422

def test_missing_text_field_422():
    response = client.post("/analyze", json={})
    assert response.status_code == 422

def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
