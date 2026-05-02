from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_analyze_normal_sentence():
    response = client.post("/analyze", json={"text": "Dit is een normale zin."})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Dit is een normale zin."
    assert data["letter_count"] == 18
    assert data["word_count"] == 5
    assert data["vowel_count"] == 8
    assert data["is_palindrome"] is False

def test_post_analyze_palindrome_lepel():
    response = client.post("/analyze", json={"text": "Lepel"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_palindrome"] is True

def test_post_analyze_palindrome_hallo():
    response = client.post("/analyze", json={"text": "hallo"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_palindrome"] is False

def test_post_analyze_empty_string():
    response = client.post("/analyze", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["letter_count"] == 0
    assert data["word_count"] == 0
    assert data["vowel_count"] == 0
    assert data["is_palindrome"] is True

def test_get_analyze_query_param():
    response = client.get("/analyze?text=hallo%20wereld")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "hallo wereld"
    assert data["letter_count"] == 11
    assert data["word_count"] == 2
    assert data["vowel_count"] == 4
    assert data["is_palindrome"] is False

def test_missing_text_field_422():
    response = client.post("/analyze", json={"wrong_field": "test"})
    assert response.status_code == 422

def test_get_status():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "text_analyzer_service"

def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
