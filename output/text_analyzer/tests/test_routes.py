from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_post_analyze_valid_sentence():
    # test dat POST /analyze correct het aantal letters, woorden en klinkers telt voor een geldige zin
    response = client.post("/analyze", json={"text": "Dit is een test"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Dit is een test"
    assert data["letter_count"] == 12
    assert data["word_count"] == 4
    assert data["vowel_count"] == 5
    assert data["is_palindrome"] is False

def test_post_analyze_palindrome():
    # test dat POST /analyze een palindroom correct detecteert (bv. 'Lepel' of 'racecar')
    response1 = client.post("/analyze", json={"text": "Lepel"})
    assert response1.status_code == 200
    assert response1.json()["is_palindrome"] is True

    response2 = client.post("/analyze", json={"text": "racecar"})
    assert response2.status_code == 200
    assert response2.json()["is_palindrome"] is True

def test_post_analyze_non_palindrome():
    # test dat POST /analyze niet-palindromen correct herkent
    response = client.post("/analyze", json={"text": "Hallo"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is False

def test_get_analyze_query_param():
    # test dat GET /analyze met query parameter correct werkt
    response = client.get("/analyze?text=Hallo%20wereld")
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Hallo wereld"
    assert data["letter_count"] == 11
    assert data["word_count"] == 2
    assert data["vowel_count"] == 4
    assert data["is_palindrome"] is False

def test_post_analyze_missing_text():
    # test dat POST /analyze zonder 'text' veld een 422 status geeft
    response = client.post("/analyze", json={"wrong_field": "test"})
    assert response.status_code == 422

def test_empty_string_handling():
    # test dat een lege string correct wordt afgehandeld (0 letters, 0 woorden)
    response = client.post("/analyze", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["letter_count"] == 0
    assert data["word_count"] == 0
    assert data["vowel_count"] == 0

def test_palindrome_ignores_case_and_spaces():
    # test dat hoofdletters en spaties genegeerd worden bij palindroom detectie
    response = client.post("/analyze", json={"text": "Was it a car or a cat I saw"})
    assert response.status_code == 200
    assert response.json()["is_palindrome"] is True

def test_get_status():
    # test dat GET /status een 200 met status ok teruggeeft
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_health():
    # test dat GET /health een 200 met status ok teruggeeft (volgens kritische regel 0)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
