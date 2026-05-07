def test_post_validate_isbn13(client):
    response = client.post("/validate", json={"isbn": "978-3-16-148410-0"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["format"] == "ISBN-13"
    assert data["normalized"] == "9783161484100"
    assert data["input"] == "978-3-16-148410-0"

def test_post_validate_isbn10(client):
    response = client.post("/validate", json={"isbn": "0-306-40615-2"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["format"] == "ISBN-10"

def test_post_validate_hyphens_spaces(client):
    response = client.post("/validate", json={"isbn": "978 3 16 148410 0"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["normalized"] == "9783161484100"

def test_post_validate_isbn10_x(client):
    response = client.post("/validate", json={"isbn": "0-8044-2957-X"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["format"] == "ISBN-10"

def test_post_validate_invalid_checksum(client):
    response = client.post("/validate", json={"isbn": "978-3-16-148410-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["format"] == "ISBN-13"

def test_post_validate_invalid_length(client):
    response = client.post("/validate", json={"isbn": "12345"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["format"] is None

def test_post_validate_missing_field(client):
    response = client.post("/validate", json={"wrong_field": "123"})
    assert response.status_code == 422

def test_get_validate_query_param(client):
    response = client.get("/validate?isbn=0306406152")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["format"] == "ISBN-10"

def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
