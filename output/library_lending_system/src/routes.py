from fastapi import APIRouter, HTTPException
from typing import List
from src.models import BookCreate, BookResponse, MemberCreate, MemberResponse, LoanCreate, LoanResponse
import src.logic as logic

router = APIRouter()

@router.post("/books", response_model=BookResponse)
def create_book(book: BookCreate):
    return logic.add_book(book.model_dump())

@router.get("/books", response_model=List[BookResponse])
def get_books():
    return logic.get_all_books()

@router.get("/books/{id}", response_model=BookResponse)
def get_book(id: int):
    book = logic.get_book(id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.post("/members", response_model=MemberResponse)
def create_member(member: MemberCreate):
    try:
        return logic.add_member(member.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/members/{id}", response_model=MemberResponse)
def get_member(id: int):
    member = logic.get_member(id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.post("/loans", response_model=LoanResponse)
def create_loan(loan: LoanCreate):
    try:
        created_loan = logic.create_loan(loan.book_id, loan.member_id)
        return logic.enrich_loan_with_overdue(created_loan)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/loans/{id}/return", response_model=LoanResponse)
def return_loan(id: int):
    try:
        returned_loan = logic.return_loan(id)
        return logic.enrich_loan_with_overdue(returned_loan)
    except ValueError as e:
        if str(e) == "Loan not found":
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/loans", response_model=List[LoanResponse])
def get_active_loans():
    loans = logic.get_active_loans()
    return [logic.enrich_loan_with_overdue(l) for l in loans]

@router.get("/members/{id}/loans", response_model=List[LoanResponse])
def get_member_loans(id: int):
    member = logic.get_member(id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    loans = logic.get_member_loans(id)
    return [logic.enrich_loan_with_overdue(l) for l in loans]
