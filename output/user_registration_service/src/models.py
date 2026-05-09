from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9]+$")

class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    created_at: datetime

class User(UserPublic):
    api_key: UUID

class UserList(BaseModel):
    users: list[UserPublic]

class UserDeleteResponse(BaseModel):
    deleted: bool
    id: UUID
