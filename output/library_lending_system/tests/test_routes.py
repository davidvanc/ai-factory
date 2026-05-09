import pytest
from src.database import reset_state
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def _reset_state_between_tests():
    reset_state()
    yield

def test_post_books_creates_book(client):
    response = client.post("/books", json={
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "isbn": "9780743273565",
        "total_copies": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["available_copies"] == 3
    assert data["total_copies"] == 3
    assert data["title"] == "The Great Gatsby"

def test_get_books_returns_all(client):
    client.post("/books", json={"title": "Book 1", "author": "A1", "isbn": "1", "total_copies": 1})
    client.post("/books", json={"title": "Book 2", "author": "A2", "isbn": "2", "total_copies": 2})
    
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_book_not_found(client):
    response = client.get("/books/999")
    assert response.status_code == 404

def test_post_members_valid_email(client):
    response = client.post("/members", json={
        "name": "Alice Smith",
        "email": "alice@example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"

def test_post_members_invalid_email(client):
    response = client.post("/members", json={
        "name": "Bob",
        "email": "not-an-email"
    })
    assert response.status_code == 422

def test_post_members_duplicate_email(client):
    client.post("/members", json={"name": "Alice", "email": "alice@example.com"})
    response = client.post("/members", json={"name": "Alice 2", "email": "alice@example.com"})
    assert response.status_code == 422

def test_get_member_not_found(client):
    response = client.get("/members/999")
    assert response.status_code == 404

def test_post_loans_creates_loan_and_decrements_copies(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 2})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    
    response = client.post("/loans", json={"book_id": 1, "member_id": 1})
    assert response.status_code == 200
    data = response.json()
    
    loaned_at = datetime.fromisoformat(data["loaned_at"].replace("Z", "+00:00"))
    due_at = datetime.fromisoformat(data["due_at"].replace("Z", "+00:00"))
    assert (due_at - loaned_at).days == 14
    
    book_resp = client.get("/books/1")
    assert book_resp.json()["available_copies"] == 1

def test_post_loans_max_3_active(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 5})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    
    response = client.post("/loans", json={"book_id": 1, "member_id": 1})
    assert response.status_code == 422

def test_post_loans_no_available_copies(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 1})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/members", json={"name": "M2", "email": "m2@example.com"})
    
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    response = client.post("/loans", json={"book_id": 1, "member_id": 2})
    assert response.status_code == 422

def test_post_loans_return(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 1})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    
    response = client.post("/loans/1/return")
    assert response.status_code == 200
    assert response.json()["returned_at"] is not None
    
    book_resp = client.get("/books/1")
    assert book_resp.json()["available_copies"] == 1

def test_post_loans_return_already_returned(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 1})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans/1/return")
    
    response = client.post("/loans/1/return")
    assert response.status_code == 422

def test_get_loans_active_only(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 2})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans/1/return")
    
    response = client.get("/loans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 2

def test_get_member_loans(client):
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 2})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/members", json={"name": "M2", "email": "m2@example.com"})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    client.post("/loans", json={"book_id": 1, "member_id": 2})
    
    response = client.get("/members/1/loans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["member_id"] == 1

def test_is_overdue(client):
    import src.logic as logic
    from src.database import _loans
    
    client.post("/books", json={"title": "B1", "author": "A1", "isbn": "1", "total_copies": 1})
    client.post("/members", json={"name": "M1", "email": "m1@example.com"})
    client.post("/loans", json={"book_id": 1, "member_id": 1})
    
    _loans[1]["due_at"] = logic.get_now() - timedelta(days=1)
    
    response = client.get("/loans")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["is_overdue"] is True
