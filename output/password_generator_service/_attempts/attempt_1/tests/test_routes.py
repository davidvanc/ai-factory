def test_generate_password_success(client):
    payload = {
        "length": 16,
        "include_digits": True,
        "include_uppercase": True,
        "include_lowercase": True,
        "include_symbols": True
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "password" in data
    assert data["length"] == 16
    assert len(data["password"]) == 16

def test_generate_password_includes_digit(client):
    payload = {
        "length": 16,
        "include_digits": True,
        "include_uppercase": False,
        "include_lowercase": False,
        "include_symbols": False
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    pwd = response.json()["password"]
    assert any(c.isdigit() for c in pwd)

def test_generate_password_includes_uppercase(client):
    payload = {
        "length": 16,
        "include_digits": False,
        "include_uppercase": True,
        "include_lowercase": False,
        "include_symbols": False
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    pwd = response.json()["password"]
    assert any(c.isupper() for c in pwd)

def test_generate_password_includes_lowercase(client):
    payload = {
        "length": 16,
        "include_digits": False,
        "include_uppercase": False,
        "include_lowercase": True,
        "include_symbols": False
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    pwd = response.json()["password"]
    assert any(c.islower() for c in pwd)

def test_generate_password_includes_symbols(client):
    payload = {
        "length": 16,
        "include_digits": False,
        "include_uppercase": False,
        "include_lowercase": False,
        "include_symbols": True
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    pwd = response.json()["password"]
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    assert any(c in symbols for c in pwd)

def test_generate_password_length_too_short(client):
    payload = {
        "length": 7,
        "include_digits": True,
        "include_uppercase": True,
        "include_lowercase": True,
        "include_symbols": True
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422

def test_generate_password_length_too_long(client):
    payload = {
        "length": 129,
        "include_digits": True,
        "include_uppercase": True,
        "include_lowercase": True,
        "include_symbols": True
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 422

def test_generate_password_no_groups(client):
    payload = {
        "length": 16,
        "include_digits": False,
        "include_uppercase": False,
        "include_lowercase": False,
        "include_symbols": False
    }
    response = client.post("/generate", json=payload)
    assert response.status_code in [400, 422]

def test_generate_password_consecutive_calls_different(client):
    payload = {
        "length": 16,
        "include_digits": True,
        "include_uppercase": True,
        "include_lowercase": True,
        "include_symbols": True
    }
    response1 = client.post("/generate", json=payload)
    response2 = client.post("/generate", json=payload)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["password"] != response2.json()["password"]

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
