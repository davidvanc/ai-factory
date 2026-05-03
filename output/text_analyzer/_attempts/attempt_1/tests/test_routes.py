from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_analyze_letter_count():
    # test dat POST /analyze het correcte aantal letters teruggeeft voor een zin
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["letter_count"] == 13

def test_post_analyze_word_count():
    # test dat POST /analyze het correcte aantal woorden teruggeeft
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["word_count"] == 3

def test_post_analyze_vowel_count():
    # test dat POST /analyze het correcte aantal klinkers teruggeeft (inclusief hoofdletters)
    response = client.post("/analyze", json={"text": "Racecar is snel"})
    assert response.status_code == 200
    assert response.json()["vowel_count"] == 5

def test_post_analyze_palindrome_lepel():
    # test dat POST /analyze is_palindrome=true teruggeeft voor 'lepel'
    response = client.post("/analyze", json={"text": "lepel"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is True

def test_post_analyze_palindrome_race_car():
    # test dat POST /analyze is_palindrome=true teruggeeft voor 'Race car' (spaties en case negeren)
    response = client.post("/analyze", json={"text": "Race car"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is True

def test_post_analyze_palindrome_false():
    # test dat POST /analyze is_palindrome=false teruggeeft voor 'hallo'
    response = client.post("/analyze", json={"text": "hallo"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is False

def test_get_analyze_query_param():
    # test dat GET /analyze werkt met een query parameter
    response = client.get("/analyze?text=lepel")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "lepel"
    assert data["letter_count"] == 5
    assert data["word_count"] == 1
    assert data["vowel_count"] == 2
    assert data["is_palindrome"] is True

def test_empty_string_422():
    # test dat een lege string een 422 of nette foutmelding geeft
    response_post = client.post("/analyze", json={"text": ""})
    assert response_post.status_code == 422
    
    response_get = client.get("/analyze?text=")
    assert response_get.status_code == 422

def test_missing_text_field_422():
    # test dat ontbrekende 'text' veld een 422 status geeft
    response = client.post("/analyze", json={})
    assert response.status_code == 422

def test_get_health():
    # test dat GET /health status 'ok' teruggeeft
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
