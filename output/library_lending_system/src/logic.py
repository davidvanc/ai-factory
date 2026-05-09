from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from src.models import BookCreate, MemberCreate, LoanCreate
from src.database import _books, _members, _loans
import src.database as db

def get_now():
    return datetime.now(timezone.utc)

def create_book(book: BookCreate) -> dict:
    db._book_counter += 1
    book_id = db._book_counter
    book_data = book.model_dump()
    book_data.update({
        "id": book_id,
        "available_copies": book.total_copies,
        "added_at": get_now()
    })
    _books[book_id] = book_data
    return book_data

def get_books() -> list:
    return list(_books.values())

def get_book(book_id: int) -> dict:
    if book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    return _books[book_id]

def create_member(member: MemberCreate) -> dict:
    for m in _members.values():
        if m["email"] == member.email:
            raise HTTPException(status_code=422, detail="Email already registered")
    
    db._member_counter += 1
    member_id = db._member_counter
    member_data = member.model_dump()
    member_data.update({
        "id": member_id,
        "registered_at": get_now()
    })
    _members[member_id] = member_data
    return member_data

def get_member(member_id: int) -> dict:
    if member_id not in _members:
        raise HTTPException(status_code=404, detail="Member not found")
    return _members[member_id]

def calculate_is_overdue(loan: dict) -> bool:
    if loan["returned_at"] is not None:
        return False
    return get_now() > loan["due_at"]

def format_loan(loan: dict) -> dict:
    loan_copy = loan.copy()
    loan_copy["is_overdue"] = calculate_is_overdue(loan)
    return loan_copy

def create_loan(loan: LoanCreate) -> dict:
    if loan.book_id not in _books:
        raise HTTPException(status_code=404, detail="Book not found")
    if loan.member_id not in _members:
        raise HTTPException(status_code=404, detail="Member not found")
    
    book = _books[loan.book_id]
    if book["available_copies"] <= 0:
        raise HTTPException(status_code=422, detail="No available copies")
    
    active_loans = [l for l in _loans.values() if l["member_id"] == loan.member_id and l["returned_at"] is None]
    if len(active_loans) >= 3:
        raise HTTPException(status_code=422, detail="Member already has 3 active loans")
    
    book["available_copies"] -= 1
    
    db._loan_counter += 1
    loan_id = db._loan_counter
    now = get_now()
    loan_data = {
        "id": loan_id,
        "book_id": loan.book_id,
        "member_id": loan.member_id,
        "loaned_at": now,
        "due_at": now + timedelta(days=14),
        "returned_at": None
    }
    _loans[loan_id] = loan_data
    return format_loan(loan_data)

def return_loan(loan_id: int) -> dict:
    if loan_id not in _loans:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    loan = _loans[loan_id]
    if loan["returned_at"] is not None:
        raise HTTPException(status_code=422, detail="Loan already returned")
    
    loan["returned_at"] = get_now()
    book = _books[loan["book_id"]]
    book["available_copies"] += 1
    
    return format_loan(loan)

def get_active_loans() -> list:
    return [format_loan(l) for l in _loans.values() if l["returned_at"] is None]

def get_member_loans(member_id: int) -> list:
    if member_id not in _members:
        raise HTTPException(status_code=404, detail="Member not found")
    return [format_loan(l) for l in _loans.values() if l["member_id"] == member_id]
