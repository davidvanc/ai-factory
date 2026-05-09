import pytest
from src.logic import clear_todos

@pytest.fixture(autouse=True)
def reset_state():
    clear_todos()
    yield

def test_post_todos_creates_todo_and_returns_id(client):
    response = client.post("/todos", json={"title": "Boodschappen doen"})
    assert response.status_code in (200, 201)
    data = response.json()
    assert "id" in data
    assert data["title"] == "Boodschappen doen"
    assert data["done"] is False

def test_post_todos_without_title_gives_422(client):
    response = client.post("/todos", json={})
    assert response.status_code == 422

def test_get_todos_returns_all_todos(client):
    client.post("/todos", json={"title": "Todo 1"})
    client.post("/todos", json={"title": "Todo 2"})
    
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"

def test_get_todo_by_id_returns_specific_todo(client):
    create_resp = client.post("/todos", json={"title": "Specifieke Todo"})
    todo_id = create_resp.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Specifieke Todo"

def test_get_todo_by_id_gives_404_for_non_existent_id(client):
    response = client.get("/todos/9999")
    assert response.status_code == 404

def test_patch_todo_updates_done_status(client):
    create_resp = client.post("/todos", json={"title": "Patch Todo"})
    todo_id = create_resp.json()["id"]
    
    response = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert response.status_code == 200
    data = response.json()
    assert data["done"] is True
    
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.json()["done"] is True

def test_patch_todo_gives_404_for_non_existent_id(client):
    response = client.patch("/todos/9999", json={"done": True})
    assert response.status_code == 404

def test_delete_todo_removes_todo(client):
    create_resp = client.post("/todos", json={"title": "Delete Todo"})
    todo_id = create_resp.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Todo deleted", "id": todo_id}
    
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404

def test_delete_todo_gives_404_for_non_existent_id(client):
    response = client.delete("/todos/9999")
    assert response.status_code == 404
