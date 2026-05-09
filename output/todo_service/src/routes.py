from fastapi import APIRouter, HTTPException
from typing import List
from src.models import TodoCreate, TodoResponse, TodoDeleteResponse
from src.logic import (
    get_all_todos,
    get_todo_by_id,
    create_todo,
    mark_todo_done,
    delete_todo
)
from src.service_template.logging_config import get_logger

log = get_logger("todo_routes")
router = APIRouter()

@router.post("/todos", response_model=TodoResponse)
def api_create_todo(todo: TodoCreate):
    log.info(f"Creating new todo with title: {todo.title}")
    return create_todo(todo)

@router.get("/todos", response_model=List[TodoResponse])
def api_get_todos():
    log.info("Fetching all todos")
    return get_all_todos()

@router.get("/todos/{todo_id}", response_model=TodoResponse)
def api_get_todo(todo_id: int):
    log.info(f"Fetching todo {todo_id}")
    todo = get_todo_by_id(todo_id)
    if not todo:
        log.warning(f"Todo {todo_id} not found")
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/todos/{todo_id}", response_model=TodoResponse)
def api_mark_done(todo_id: int):
    log.info(f"Marking todo {todo_id} as done")
    todo = mark_todo_done(todo_id)
    if not todo:
        log.warning(f"Todo {todo_id} not found for patch")
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.delete("/todos/{todo_id}", response_model=TodoDeleteResponse)
def api_delete_todo(todo_id: int):
    log.info(f"Deleting todo {todo_id}")
    success = delete_todo(todo_id)
    if not success:
        log.warning(f"Todo {todo_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Todo not found")
    return TodoDeleteResponse(deleted=True, id=todo_id)
