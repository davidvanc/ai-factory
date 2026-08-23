import pytest
from src.logic import reverse_string

def test_logic_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("") == ""
    assert reverse_string("こんにちは") == "はちにんこ"

def test_post_reverse_correctly_reverses(client):
    response = client.post("/reverse", json={"text": "hello world"})
    assert response.status_code == 200
    assert response.json() == {"reversed": "dlrow olleh"}

def test_post_reverse_empty_string(client):
    response = client.post("/reverse", json={"text": ""})
    assert response.status_code == 200
    assert response.json() == {"reversed": ""}

def test_post_reverse_unicode(client):
    response = client.post("/reverse", json={"text": "こんにちは"})
    assert response.status_code == 200
    assert response.json() == {"reversed": "はちにんこ"}

def test_post_reverse_missing_text(client):
    response = client.post("/reverse", json={"wrong_field": "hello"})
    assert response.status_code == 422

def test_post_reverse_non_string(client):
    response = client.post("/reverse", json={"text": 123})
    assert response.status_code == 422
    
    response2 = client.post("/reverse", json={"text": ["list"]})
    assert response2.status_code == 422
