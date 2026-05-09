from fastapi import APIRouter
from typing import List
from src.models import BookCreate, BookResponse, MemberCreate, MemberResponse, LoanCreate, LoanResponse
import src.logic as logic

router = APIRouter()

@router.post("/books", response_model=BookResponse)
def create_book(book: BookCreate):
    return logic.create_book(book)

@router.get("/books", response_model=List[BookResponse])
def get_books():
    return logic.get_books()

@router.get("/books/{id}", response_model=BookResponse)
def get_book(id: int):
    return logic.get_book(id)

@router.post("/members", response_model=MemberResponse)
def create_member(member: MemberCreate):
    return logic.create_member(member)

@router.get("/members/{id}", response_model=MemberResponse)
def get_member(id: int):
    return logic.get_member(id)

@router.post("/loans", response_model=LoanResponse)
def create_loan(loan: LoanCreate):
    return logic.create_loan(loan)

@router.post("/loans/{id}/return", response_model=LoanResponse)
def return_loan(id: int):
    return logic.return_loan(id)

@router.get("/loans", response_model=List[LoanResponse])
def get_active_loans():
    return logic.get_active_loans()

@router.get("/members/{id}/loans", response_model=List[LoanResponse])
def get_member_loans(id: int):
    return logic.get_member_loans(id)
