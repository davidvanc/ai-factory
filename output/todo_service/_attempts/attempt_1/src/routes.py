from fastapi import APIRouter, HTTPException
from typing import List
from src.models import TodoCreate, TodoUpdate, TodoResponse
from src import logic

router = APIRouter(prefix="/todos", tags=["todos"])

@router.post("", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    return logic.create_todo(todo)

@router.get("", response_model=List[TodoResponse])
def get_todos():
    return logic.get_all_todos()

@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    todo = logic.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    todo = logic.update_todo(todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.delete("/{todo_id}")
def delete_todo(todo_id: int):
    success = logic.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted", "id": todo_id}
