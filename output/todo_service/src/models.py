from pydantic import BaseModel
from datetime import datetime

class TodoCreate(BaseModel):
    title: str

class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime

class TodoDeleteResponse(BaseModel):
    deleted: bool
    id: int
