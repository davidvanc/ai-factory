def test_validate_valid_email(client):
    response = client.post("/validate", json={"email": "john.doe@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["reason"] == "valid email address"

def test_validate_consecutive_dots(client):
    response = client.post("/validate", json={"email": "john..doe@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "consecutive dots" in data["reason"].lower()

def test_validate_no_tld(client):
    response = client.post("/validate", json={"email": "user@localhost"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "tld" in data["reason"].lower()

def test_validate_invalid_characters(client):
    response = client.post("/validate", json={"email": "user!#@exa mple.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "invalid characters" in data["reason"].lower()

def test_validate_no_at_symbol(client):
    response = client.post("/validate", json={"email": "johndoeexample.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "@ symbol" in data["reason"].lower()

def test_validate_empty_string(client):
    response = client.post("/validate", json={"email": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "empty" in data["reason"].lower()

def test_validate_missing_email_field(client):
    response = client.post("/validate", json={"not_email": "john@example.com"})
    assert response.status_code == 422
