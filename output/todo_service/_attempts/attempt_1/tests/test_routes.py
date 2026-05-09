import pytest
from src.logic import clear_todos, create_todo, get_all_todos, get_todo_by_id, update_todo, delete_todo
from src.models import TodoCreate, TodoUpdate

@pytest.fixture(autouse=True)
def reset_todos():
    clear_todos()
    yield

# --- Unit Tests for logic.py ---

def test_logic_create_todo():
    todo = create_todo(TodoCreate(title="Logic Test"))
    assert todo.id == 1
    assert todo.title == "Logic Test"
    assert todo.done is False

def test_logic_get_all_todos():
    create_todo(TodoCreate(title="T1"))
    create_todo(TodoCreate(title="T2"))
    todos = get_all_todos()
    assert len(todos) == 2

def test_logic_get_todo_by_id():
    todo = create_todo(TodoCreate(title="T1"))
    fetched = get_todo_by_id(todo.id)
    assert fetched is not None
    assert fetched.id == todo.id
    assert get_todo_by_id(999) is None

def test_logic_update_todo():
    todo = create_todo(TodoCreate(title="T1"))
    updated = update_todo(todo.id, TodoUpdate(done=True))
    assert updated is not None
    assert updated.done is True
    assert update_todo(999, TodoUpdate(done=True)) is None

def test_logic_delete_todo():
    todo = create_todo(TodoCreate(title="T1"))
    assert delete_todo(todo.id) is True
    assert delete_todo(todo.id) is False

# --- Integration Tests for routes.py ---

def test_post_todos_creates_new_todo(client):
    response = client.post("/todos", json={"title": "Boodschappen doen"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Boodschappen doen"
    assert data["done"] is False
    assert "created_at" in data

def test_post_todos_without_title_gives_422(client):
    response = client.post("/todos", json={})
    assert response.status_code == 422

def test_post_todos_empty_title_edge_case(client):
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422

def test_get_todos_returns_list(client):
    client.post("/todos", json={"title": "Todo 1"})
    client.post("/todos", json={"title": "Todo 2"})
    
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"

def test_get_todo_by_id_returns_correct_todo(client):
    create_resp = client.post("/todos", json={"title": "Specific Todo"})
    todo_id = create_resp.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Specific Todo"

def test_get_todo_by_id_gives_404_for_non_existent(client):
    response = client.get("/todos/999")
    assert response.status_code == 404

def test_get_todo_invalid_id_format(client):
    response = client.get("/todos/abc")
    assert response.status_code == 422

def test_patch_todo_updates_done_status(client):
    create_resp = client.post("/todos", json={"title": "To be done"})
    todo_id = create_resp.json()["id"]
    
    response = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["done"] is True

def test_patch_todo_gives_404_for_non_existent(client):
    response = client.patch("/todos/999", json={"done": True})
    assert response.status_code == 404

def test_patch_todo_invalid_body(client):
    create_resp = client.post("/todos", json={"title": "To be done"})
    todo_id = create_resp.json()["id"]
    
    response = client.patch(f"/todos/{todo_id}", json={"done": "not-a-boolean"})
    assert response.status_code == 422

def test_delete_todo_removes_todo(client):
    create_resp = client.post("/todos", json={"title": "To be deleted"})
    todo_id = create_resp.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert data["id"] == todo_id
    
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404

def test_delete_todo_gives_404_for_non_existent(client):
    response = client.delete("/todos/999")
    assert response.status_code == 404
