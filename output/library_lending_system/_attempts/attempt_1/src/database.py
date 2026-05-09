from typing import Dict, Any

_books: Dict[int, Dict[str, Any]] = {}
_members: Dict[int, Dict[str, Any]] = {}
_loans: Dict[int, Dict[str, Any]] = {}

_book_id_counter: int = 1
_member_id_counter: int = 1
_loan_id_counter: int = 1

def reset_state() -> None:
    global _book_id_counter, _member_id_counter, _loan_id_counter
    _books.clear()
    _members.clear()
    _loans.clear()
    _book_id_counter = 1
    _member_id_counter = 1
    _loan_id_counter = 1
