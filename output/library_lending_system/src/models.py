from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    total_copies: int = Field(..., ge=1)

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    available_copies: int
    total_copies: int
    added_at: datetime

class MemberCreate(BaseModel):
    name: str
    email: EmailStr

class MemberResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    registered_at: datetime

class LoanCreate(BaseModel):
    book_id: int
    member_id: int

class LoanResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    loaned_at: datetime
    due_at: datetime
    returned_at: Optional[datetime] = None
    is_overdue: bool
