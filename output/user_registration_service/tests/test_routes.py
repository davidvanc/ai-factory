import pytest
from uuid import UUID, uuid4

def test_create_user_valid(client):
    response = client.post("/users", json={"email": "alice@example.com", "username": "alice123"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "api_key" in data
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice123"
    # Verify UUID format
    UUID(data["api_key"])
    UUID(data["id"])

def test_create_user_invalid_email(client):
    response = client.post("/users", json={"email": "invalid-email", "username": "bob123"})
    assert response.status_code == 422

def test_create_user_username_too_short(client):
    response = client.post("/users", json={"email": "short@example.com", "username": "bo"})
    assert response.status_code == 422

def test_create_user_username_too_long(client):
    response = client.post("/users", json={"email": "long@example.com", "username": "thisusernameiswaytoolong"})
    assert response.status_code == 422

def test_create_user_username_non_alphanumeric(client):
    response = client.post("/users", json={"email": "symbol@example.com", "username": "bob_123!"})
    assert response.status_code == 422

def test_create_user_duplicate_email(client):
    client.post("/users", json={"email": "dup@example.com", "username": "user1"})
    response = client.post("/users", json={"email": "dup@example.com", "username": "user2"})
    assert response.status_code == 409

def test_get_user_full_info(client):
    create_resp = client.post("/users", json={"email": "get@example.com", "username": "getuser"})
    user_id = create_resp.json()["id"]
    
    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == user_id
    assert "api_key" in data

def test_get_user_unknown_id(client):
    response = client.get(f"/users/{uuid4()}")
    assert response.status_code == 404

def test_list_users_no_api_key(client):
    client.post("/users", json={"email": "list1@example.com", "username": "listuser1"})
    client.post("/users", json={"email": "list2@example.com", "username": "listuser2"})
    
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) >= 2
    
    for user in data["users"]:
        assert "api_key" not in user
        assert "id" in user
        assert "email" in user
        assert "username" in user

def test_delete_user_success(client):
    create_resp = client.post("/users", json={"email": "del@example.com", "username": "deluser"})
    user_id = create_resp.json()["id"]
    
    del_resp = client.delete(f"/users/{user_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
    assert del_resp.json()["id"] == user_id
    
    get_resp = client.get(f"/users/{user_id}")
    assert get_resp.status_code == 404

def test_delete_user_unknown_id(client):
    response = client.delete(f"/users/{uuid4()}")
    assert response.status_code == 404
