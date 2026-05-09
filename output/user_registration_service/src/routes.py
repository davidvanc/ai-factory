from fastapi import APIRouter, HTTPException
from uuid import UUID
from src.models import UserCreate, User, UserList, UserDeleteResponse
from src.logic import (
    create_new_user, 
    retrieve_user, 
    list_all_users, 
    remove_user, 
    DuplicateEmailError, 
    UserNotFoundError
)

router = APIRouter()

@router.post("/users", response_model=User)
def create_user_endpoint(user_in: UserCreate):
    try:
        return create_new_user(user_in)
    except DuplicateEmailError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/users", response_model=UserList)
def list_users_endpoint():
    users = list_all_users()
    return UserList(users=users)

@router.get("/users/{user_id}", response_model=User)
def get_user_endpoint(user_id: UUID):
    try:
        return retrieve_user(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/users/{user_id}", response_model=UserDeleteResponse)
def delete_user_endpoint(user_id: UUID):
    try:
        remove_user(user_id)
        return UserDeleteResponse(deleted=True, id=user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
