from src.logic import reverse_string

def test_logic_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    assert reverse_string("こんにちは") == "はちにんこ"

def test_reverse_string_correctly(client):
    response = client.post("/reverse", json={"text": "hello world"})
    assert response.status_code == 200
    assert response.json() == {"reversed": "dlrow olleh"}

def test_reverse_empty_string(client):
    response = client.post("/reverse", json={"text": ""})
    assert response.status_code == 200
    assert response.json() == {"reversed": ""}

def test_reverse_unicode_characters(client):
    response = client.post("/reverse", json={"text": "こんにちは"})
    assert response.status_code == 200
    assert response.json() == {"reversed": "はちにんこ"}

def test_missing_text_field(client):
    response = client.post("/reverse", json={})
    assert response.status_code == 422

def test_non_string_value(client):
    # Test met een integer
    response = client.post("/reverse", json={"text": 123})
    assert response.status_code == 422
    
    # Test met een list
    response = client.post("/reverse", json={"text": ["a", "b"]})
    assert response.status_code == 422
