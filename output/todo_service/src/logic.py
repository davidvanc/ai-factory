from datetime import datetime
from src.models import Todo
from src.service_template.logging_config import get_logger

log = get_logger("todo_logic")

_todos: dict[int, Todo] = {}
_current_id: int = 1

def create_todo(title: str) -> Todo:
    global _current_id
    todo = Todo(
        id=_current_id,
        title=title,
        done=False,
        created_at=datetime.now()
    )
    _todos[_current_id] = todo
    _current_id += 1
    log.info(f"Created todo with id {todo.id}")
    return todo

def get_todos() -> list[Todo]:
    return list(_todos.values())

def get_todo(todo_id: int) -> Todo | None:
    return _todos.get(todo_id)

def update_todo(todo_id: int, done: bool) -> Todo | None:
    todo = _todos.get(todo_id)
    if todo:
        todo.done = done
        _todos[todo_id] = todo
        log.info(f"Updated todo {todo_id} done status to {done}")
    return todo

def delete_todo(todo_id: int) -> bool:
    if todo_id in _todos:
        del _todos[todo_id]
        log.info(f"Deleted todo {todo_id}")
        return True
    return False

def clear_todos() -> None:
    global _todos, _current_id
    _todos.clear()
    _current_id = 1
