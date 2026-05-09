from typing import List, Optional, Dict
from datetime import datetime
from src.models import TodoCreate, TodoResponse

todos_db: Dict[int, TodoResponse] = {}
current_id: int = 1

def get_all_todos() -> List[TodoResponse]:
    return list(todos_db.values())

def get_todo_by_id(todo_id: int) -> Optional[TodoResponse]:
    return todos_db.get(todo_id)

def create_todo(todo_in: TodoCreate) -> TodoResponse:
    global current_id
    new_todo = TodoResponse(
        id=current_id,
        title=todo_in.title,
        done=False,
        created_at=datetime.now()
    )
    todos_db[current_id] = new_todo
    current_id += 1
    return new_todo

def mark_todo_done(todo_id: int) -> Optional[TodoResponse]:
    todo = todos_db.get(todo_id)
    if todo:
        todo.done = True
    return todo

def delete_todo(todo_id: int) -> bool:
    if todo_id in todos_db:
        del todos_db[todo_id]
        return True
    return False

def clear_db():
    global current_id
    todos_db.clear()
    current_id = 1
