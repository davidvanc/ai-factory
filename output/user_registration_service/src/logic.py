from uuid import uuid4, UUID
from datetime import datetime, timezone
from src.models import UserCreate, User, UserPublic
from src.storage import save_user, get_user, get_user_by_email, get_all_users, delete_user

class DuplicateEmailError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

def create_new_user(data: UserCreate) -> User:
    if get_user_by_email(data.email):
        raise DuplicateEmailError("Email already registered")

    user = User(
        id=uuid4(),
        email=data.email,
        username=data.username,
        api_key=uuid4(),
        created_at=datetime.now(timezone.utc)
    )
    save_user(user)
    return user

def retrieve_user(user_id: UUID) -> User:
    user = get_user(user_id)
    if not user:
        raise UserNotFoundError("User not found")
    return user

def list_all_users() -> list[UserPublic]:
    users = get_all_users()
    return [UserPublic(**user.model_dump()) for user in users]

def remove_user(user_id: UUID) -> None:
    if not delete_user(user_id):
        raise UserNotFoundError("User not found")
