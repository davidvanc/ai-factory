import pytest
from datetime import datetime
from src.logic import clear_db

@pytest.fixture(autouse=True)
def setup_teardown():
    clear_db()
    yield
    clear_db()

def test_dat_POST_todos_een_nieuwe_todo_aanmaakt_en_een_id_retourneert(client):
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Buy milk"
    assert data["done"] is False

def test_dat_POST_todos_zonder_title_een_422_status_geeft(client):
    response = client.post("/todos", json={})
    assert response.status_code == 422

def test_dat_GET_todos_een_lijst_van_alle_todos_retourneert(client):
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"

def test_dat_GET_todos_id_de_juiste_todo_teruggeeft(client):
    create_resp = client.post("/todos", json={"title": "Specific Task"})
    todo_id = create_resp.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Task"
    assert response.json()["id"] == todo_id

def test_dat_GET_todos_id_een_404_geeft_voor_onbestaand_id(client):
    response = client.get("/todos/9999")
    assert response.status_code == 404

def test_dat_PATCH_todos_id_de_todo_als_done_markeert(client):
    create_resp = client.post("/todos", json={"title": "To be done"})
    todo_id = create_resp.json()["id"]
    
    response = client.patch(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["done"] is True
    
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.json()["done"] is True

def test_dat_PATCH_todos_id_een_404_geeft_voor_onbestaand_id(client):
    response = client.patch("/todos/9999")
    assert response.status_code == 404

def test_dat_DELETE_todos_id_de_todo_verwijdert(client):
    create_resp = client.post("/todos", json={"title": "To be deleted"})
    todo_id = create_resp.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert response.json()["id"] == todo_id
    
    get_resp = client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404

def test_dat_DELETE_todos_id_een_404_geeft_voor_onbestaand_id(client):
    response = client.delete("/todos/9999")
    assert response.status_code == 404

def test_dat_created_at_een_geldig_ISO_timestamp_is(client):
    response = client.post("/todos", json={"title": "Timestamp test"})
    assert response.status_code == 200
    created_at = response.json()["created_at"]
    
    clean_timestamp = created_at.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean_timestamp)
        assert isinstance(dt, datetime)
    except ValueError:
        pytest.fail(f"'{created_at}' is not a valid ISO timestamp")
