import pytest
from datetime import datetime
from src.logic import clear_todos, create_todo, get_todo, update_todo, delete_todo

@pytest.fixture(autouse=True)
def reset_state():
    clear_todos()
    yield

# --- Unit Tests ---
def test_logic_create_and_get_todo():
    todo = create_todo("Logic Task")
    assert todo.title == "Logic Task"
    assert todo.done is False
    
    fetched = get_todo(todo.id)
    assert fetched is not None
    assert fetched.id == todo.id

def test_logic_update_and_delete_todo():
    todo = create_todo("To be updated")
    updated = update_todo(todo.id, True)
    assert updated is not None
    assert updated.done is True
    
    assert delete_todo(todo.id) is True
    assert get_todo(todo.id) is None
    assert delete_todo(todo.id) is False

# --- Integration Tests ---
def test_post_todos_creates_new_todo_and_returns_id(client):
    response = client.post("/todos", json={"title": "Buy groceries"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Buy groceries"
    assert data["done"] is False

def test_post_todos_without_title_gives_422(client):
    response = client.post("/todos", json={})
    assert response.status_code == 422

def test_get_todos_returns_list_with_created_todos(client):
    client.post("/todos", json={"title": "Task 1"})
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Task 1"

def test_get_todo_by_id_returns_correct_todo(client):
    post_resp = client.post("/todos", json={"title": "Specific Task"})
    todo_id = post_resp.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Task"

def test_get_todo_by_id_gives_404_for_unknown_id(client):
    response = client.get("/todos/999")
    assert response.status_code == 404

def test_patch_todo_by_id_updates_done_status_to_true(client):
    post_resp = client.post("/todos", json={"title": "Patch Task"})
    todo_id = post_resp.json()["id"]
    
    response = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert response.status_code == 200
    assert response.json()["done"] is True

def test_patch_todo_by_id_gives_404_for_unknown_id(client):
    response = client.patch("/todos/999", json={"done": True})
    assert response.status_code == 404

def test_delete_todo_by_id_removes_todo(client):
    post_resp = client.post("/todos", json={"title": "Delete Task"})
    todo_id = post_resp.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True, "id": todo_id}
    
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404

def test_delete_todo_by_id_gives_404_for_unknown_id(client):
    response = client.delete("/todos/999")
    assert response.status_code == 404

def test_created_at_contains_valid_iso_timestamp(client):
    post_resp = client.post("/todos", json={"title": "Time Task"})
    created_at_str = post_resp.json()["created_at"]
    dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    assert dt is not None
