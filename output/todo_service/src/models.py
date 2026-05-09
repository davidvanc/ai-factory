from pydantic import BaseModel, Field
from datetime import datetime

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1)

class TodoUpdate(BaseModel):
    done: bool

class Todo(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime
