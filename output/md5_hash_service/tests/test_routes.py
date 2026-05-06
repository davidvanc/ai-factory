from src.logic import calculate_md5

def test_post_hash_hello_world(client):
    response = client.post("/hash", json={"text": "hello world"})
    assert response.status_code == 200
    assert response.json() == {"text": "hello world", "md5": "5eb63bbbe01eeed093cb22bb8f5acdc3"}

def test_post_hash_empty_string(client):
    response = client.post("/hash", json={"text": ""})
    assert response.status_code == 200
    assert response.json() == {"text": "", "md5": "d41d8cd98f00b204e9800998ecf8427e"}

def test_post_hash_missing_text(client):
    response = client.post("/hash", json={})
    assert response.status_code == 422

def test_get_hash_hello_world(client):
    response = client.get("/hash?text=hello%20world")
    assert response.status_code == 200
    assert response.json() == {"text": "hello world", "md5": "5eb63bbbe01eeed093cb22bb8f5acdc3"}

def test_get_hash_missing_text(client):
    response = client.get("/hash")
    assert response.status_code == 200
    assert response.json() == {"text": "", "md5": "d41d8cd98f00b204e9800998ecf8427e"}

def test_get_status(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_calculate_md5_logic():
    assert calculate_md5("hello world") == "5eb63bbbe01eeed093cb22bb8f5acdc3"
    assert calculate_md5("") == "d41d8cd98f00b204e9800998ecf8427e"
