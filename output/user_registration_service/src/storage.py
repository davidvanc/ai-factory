from uuid import UUID
from src.models import User

_users: dict[UUID, User] = {}

def save_user(user: User) -> None:
    _users[user.id] = user

def get_user(user_id: UUID) -> User | None:
    return _users.get(user_id)

def get_user_by_email(email: str) -> User | None:
    for user in _users.values():
        if user.email == email:
            return user
    return None

def get_all_users() -> list[User]:
    return list(_users.values())

def delete_user(user_id: UUID) -> bool:
    if user_id in _users:
        del _users[user_id]
        return True
    return False
