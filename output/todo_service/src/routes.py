from fastapi import APIRouter, HTTPException
from src.models import Todo, TodoCreate, TodoUpdate
from src.logic import create_todo, get_todos, get_todo, update_todo, delete_todo

router = APIRouter()

@router.post("/todos", response_model=Todo)
def create_todo_endpoint(todo: TodoCreate):
    return create_todo(todo.title)

@router.get("/todos", response_model=list[Todo])
def get_todos_endpoint():
    return get_todos()

@router.get("/todos/{id}", response_model=Todo)
def get_todo_endpoint(id: int):
    todo = get_todo(id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.patch("/todos/{id}", response_model=Todo)
def update_todo_endpoint(id: int, todo_update: TodoUpdate):
    todo = update_todo(id, todo_update.done)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.delete("/todos/{id}")
def delete_todo_endpoint(id: int):
    success = delete_todo(id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"deleted": True, "id": id}
