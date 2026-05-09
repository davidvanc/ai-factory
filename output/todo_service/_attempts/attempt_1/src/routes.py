from fastapi import APIRouter, HTTPException
from typing import List
from src.models import TodoCreate, TodoUpdate, TodoResponse
from src import logic
from src.service_template.logging_config import get_logger

log = get_logger("todo_routes")
router = APIRouter(tags=["todos"])

@router.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    log.info(f"Creating todo: {todo.title}")
    return logic.create_todo(todo)

@router.get("/todos", response_model=List[TodoResponse])
def get_todos():
    log.info("Fetching all todos")
    return logic.get_all_todos()

@router.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    log.info(f"Fetching todo {todo_id}")
    todo = logic.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    log.info(f"Updating todo {todo_id}")
    todo = logic.update_todo(todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    log.info(f"Deleting todo {todo_id}")
    success = logic.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"deleted": True, "id": todo_id}
