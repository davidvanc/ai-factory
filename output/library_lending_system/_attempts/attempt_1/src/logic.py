from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import src.database as db

def get_now() -> datetime:
    return datetime.now(timezone.utc)

def add_book(data: Dict[str, Any]) -> Dict[str, Any]:
    book_id = db._book_id_counter
    db._book_id_counter += 1
    book = {
        "id": book_id,
        "title": data["title"],
        "author": data["author"],
        "isbn": data["isbn"],
        "available_copies": data["total_copies"],
        "total_copies": data["total_copies"],
        "added_at": get_now()
    }
    db._books[book_id] = book
    return book

def get_all_books() -> List[Dict[str, Any]]:
    return list(db._books.values())

def get_book(book_id: int) -> Optional[Dict[str, Any]]:
    return db._books.get(book_id)

def add_member(data: Dict[str, Any]) -> Dict[str, Any]:
    for m in db._members.values():
        if m["email"] == data["email"]:
            raise ValueError("Email already registered")
            
    member_id = db._member_id_counter
    db._member_id_counter += 1
    member = {
        "id": member_id,
        "name": data["name"],
        "email": data["email"],
        "registered_at": get_now()
    }
    db._members[member_id] = member
    return member

def get_member(member_id: int) -> Optional[Dict[str, Any]]:
    return db._members.get(member_id)

def create_loan(book_id: int, member_id: int) -> Dict[str, Any]:
    book = get_book(book_id)
    if not book:
        raise ValueError("Book not found")
    member = get_member(member_id)
    if not member:
        raise ValueError("Member not found")
        
    if book["available_copies"] <= 0:
        raise ValueError("Book not available")
        
    active_loans = [l for l in db._loans.values() if l["member_id"] == member_id and l["returned_at"] is None]
    if len(active_loans) >= 3:
        raise ValueError("Member has reached maximum active loans")
        
    loan_id = db._loan_id_counter
    db._loan_id_counter += 1
    now = get_now()
    loan = {
        "id": loan_id,
        "book_id": book_id,
        "member_id": member_id,
        "loaned_at": now,
        "due_at": now + timedelta(days=14),
        "returned_at": None
    }
    db._loans[loan_id] = loan
    book["available_copies"] -= 1
    return loan

def return_loan(loan_id: int) -> Dict[str, Any]:
    loan = db._loans.get(loan_id)
    if not loan:
        raise ValueError("Loan not found")
    if loan["returned_at"] is not None:
        raise ValueError("Loan already returned")
        
    loan["returned_at"] = get_now()
    book = get_book(loan["book_id"])
    if book:
        book["available_copies"] += 1
    return loan

def get_active_loans() -> List[Dict[str, Any]]:
    return [l for l in db._loans.values() if l["returned_at"] is None]

def get_member_loans(member_id: int) -> List[Dict[str, Any]]:
    return [l for l in db._loans.values() if l["member_id"] == member_id]

def enrich_loan_with_overdue(loan: Dict[str, Any]) -> Dict[str, Any]:
    is_overdue = False
    if loan["returned_at"] is None and loan["due_at"] < get_now():
        is_overdue = True
    return {**loan, "is_overdue": is_overdue}
