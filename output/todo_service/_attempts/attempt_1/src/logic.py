from typing import List, Dict, Optional
from datetime import datetime
from src.models import TodoCreate, TodoUpdate, TodoResponse

_todos: Dict[int, TodoResponse] = {}
_current_id: int = 1

def get_all_todos() -> List[TodoResponse]:
    return list(_todos.values())

def get_todo_by_id(todo_id: int) -> Optional[TodoResponse]:
    return _todos.get(todo_id)

def create_todo(todo_in: TodoCreate) -> TodoResponse:
    global _current_id
    new_todo = TodoResponse(
        id=_current_id,
        title=todo_in.title,
        done=False,
        created_at=datetime.now()
    )
    _todos[_current_id] = new_todo
    _current_id += 1
    return new_todo

def update_todo(todo_id: int, todo_in: TodoUpdate) -> Optional[TodoResponse]:
    todo = _todos.get(todo_id)
    if todo:
        todo.done = todo_in.done
        return todo
    return None

def delete_todo(todo_id: int) -> bool:
    if todo_id in _todos:
        del _todos[todo_id]
        return True
    return False

def clear_todos():
    global _todos, _current_id
    _todos.clear()
    _current_id = 1
