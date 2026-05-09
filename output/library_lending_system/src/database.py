from typing import Dict

_books: Dict[int, dict] = {}
_members: Dict[int, dict] = {}
_loans: Dict[int, dict] = {}

_book_counter: int = 0
_member_counter: int = 0
_loan_counter: int = 0

def reset_state() -> None:
    global _book_counter, _member_counter, _loan_counter
    _books.clear()
    _members.clear()
    _loans.clear()
    _book_counter = 0
    _member_counter = 0
    _loan_counter = 0
