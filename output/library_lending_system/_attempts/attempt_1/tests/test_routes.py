from datetime import datetime, timedelta, timezone
import pytest
import src.logic as logic

def test_post_books_adds_book_and_sets_available_copies(client):
    response = client.post("/books", json={
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "isbn": "9780743273565",
        "total_copies": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "The Great Gatsby"
    assert data["available_copies"] == 3
    assert data["total_copies"] == 3

def test_get_books_returns_all_books(client):
    client.post("/books", json={
        "title": "Book 1", "author": "Author 1", "isbn": "111", "total_copies": 1
    })
    client.post("/books", json={
        "title": "Book 2", "author": "Author 2", "isbn": "222", "total_copies": 2
    })
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_books_id_returns_404_for_non_existent_book(client):
    response = client.get("/books/999")
    assert response.status_code == 404

def test_post_members_registers_member_with_valid_email(client):
    response = client.post("/members", json={
        "name": "Alice Smith",
        "email": "alice@example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"

def test_post_members_returns_422_for_invalid_email_format(client):
    response = client.post("/members", json={
        "name": "Bob",
        "email": "not-an-email"
    })
    assert response.status_code == 422

def test_post_members_returns_422_for_duplicate_email(client):
    client.post("/members", json={
        "name": "Alice",
        "email": "alice@example.com"
    })
    response = client.post("/members", json={
        "name": "Alice 2",
        "email": "alice@example.com"
    })
    assert response.status_code == 422

def test_get_members_id_returns_404_for_non_existent_member(client):
    response = client.get("/members/999")
    assert response.status_code == 404

def test_post_loans_creates_loan_and_decrements_available_copies(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 2
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "member@example.com"
    })
    member_id = member_res.json()["id"]
    
    loan_res = client.post("/loans", json={
        "book_id": book_id,
        "member_id": member_id
    })
    assert loan_res.status_code == 200
    loan_data = loan_res.json()
    assert loan_data["book_id"] == book_id
    assert loan_data["member_id"] == member_id
    
    book_check = client.get(f"/books/{book_id}")
    assert book_check.json()["available_copies"] == 1

def test_post_loans_returns_422_if_member_has_3_active_loans(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 5
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "member@example.com"
    })
    member_id = member_res.json()["id"]
    
    for _ in range(3):
        client.post("/loans", json={"book_id": book_id, "member_id": member_id})
        
    loan_res = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    assert loan_res.status_code == 422

def test_post_loans_returns_422_if_book_available_copies_0(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 1
    })
    book_id = book_res.json()["id"]
    
    member1_res = client.post("/members", json={
        "name": "Member1", "email": "m1@example.com"
    })
    member1_id = member1_res.json()["id"]
    
    member2_res = client.post("/members", json={
        "name": "Member2", "email": "m2@example.com"
    })
    member2_id = member2_res.json()["id"]
    
    client.post("/loans", json={"book_id": book_id, "member_id": member1_id})
    
    loan_res = client.post("/loans", json={"book_id": book_id, "member_id": member2_id})
    assert loan_res.status_code == 422

def test_post_loans_return_marks_returned_and_increments_copies(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 1
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "m@example.com"
    })
    member_id = member_res.json()["id"]
    
    loan_res = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    loan_id = loan_res.json()["id"]
    
    return_res = client.post(f"/loans/{loan_id}/return")
    assert return_res.status_code == 200
    assert return_res.json()["returned_at"] is not None
    
    book_check = client.get(f"/books/{book_id}")
    assert book_check.json()["available_copies"] == 1

def test_post_loans_return_returns_422_if_already_returned(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 1
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "m@example.com"
    })
    member_id = member_res.json()["id"]
    
    loan_res = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    loan_id = loan_res.json()["id"]
    
    client.post(f"/loans/{loan_id}/return")
    return_res2 = client.post(f"/loans/{loan_id}/return")
    assert return_res2.status_code == 422

def test_get_loans_returns_only_active_loans(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 2
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "m@example.com"
    })
    member_id = member_res.json()["id"]
    
    loan1_res = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    loan1_id = loan1_res.json()["id"]
    
    client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    
    client.post(f"/loans/{loan1_id}/return")
    
    loans_res = client.get("/loans")
    assert loans_res.status_code == 200
    loans = loans_res.json()
    assert len(loans) == 1
    assert loans[0]["id"] != loan1_id

def test_get_members_id_loans_returns_all_loans_for_member(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 2
    })
    book_id = book_res.json()["id"]
    
    member_res = client.post("/members", json={
        "name": "Member", "email": "m@example.com"
    })
    member_id = member_res.json()["id"]
    
    loan1_res = client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    loan1_id = loan1_res.json()["id"]
    
    client.post("/loans", json={"book_id": book_id, "member_id": member_id})
    
    client.post(f"/loans/{loan1_id}/return")
    
    loans_res = client.get(f"/members/{member_id}/loans")
    assert loans_res.status_code == 200
    loans = loans_res.json()
    assert len(loans) == 2

def test_is_overdue_true_when_returned_at_null_and_due_at_in_past():
    now = datetime.now(timezone.utc)
    past_due = now - timedelta(days=1)
    loan = {
        "id": 1,
        "book_id": 1,
        "member_id": 1,
        "loaned_at": now - timedelta(days=15),
        "due_at": past_due,
        "returned_at": None
    }
    enriched = logic.enrich_loan_with_overdue(loan)
    assert enriched["is_overdue"] is True

def test_is_overdue_false_when_returned_at_not_null():
    now = datetime.now(timezone.utc)
    past_due = now - timedelta(days=1)
    loan = {
        "id": 1,
        "book_id": 1,
        "member_id": 1,
        "loaned_at": now - timedelta(days=15),
        "due_at": past_due,
        "returned_at": now
    }
    enriched = logic.enrich_loan_with_overdue(loan)
    assert enriched["is_overdue"] is False

def test_is_overdue_false_when_due_at_in_future():
    now = datetime.now(timezone.utc)
    future_due = now + timedelta(days=1)
    loan = {
        "id": 1,
        "book_id": 1,
        "member_id": 1,
        "loaned_at": now - timedelta(days=13),
        "due_at": future_due,
        "returned_at": None
    }
    enriched = logic.enrich_loan_with_overdue(loan)
    assert enriched["is_overdue"] is False

def test_get_member_loans_404(client):
    response = client.get("/members/999/loans")
    assert response.status_code == 404

def test_return_loan_404(client):
    response = client.post("/loans/999/return")
    assert response.status_code == 404

def test_create_loan_invalid_book(client):
    member_res = client.post("/members", json={
        "name": "Member", "email": "m@example.com"
    })
    member_id = member_res.json()["id"]
    response = client.post("/loans", json={"book_id": 999, "member_id": member_id})
    assert response.status_code == 422

def test_create_loan_invalid_member(client):
    book_res = client.post("/books", json={
        "title": "Book", "author": "Author", "isbn": "123", "total_copies": 2
    })
    book_id = book_res.json()["id"]
    response = client.post("/loans", json={"book_id": book_id, "member_id": 999})
    assert response.status_code == 422
