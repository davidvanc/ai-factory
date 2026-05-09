from pydantic import BaseModel, Field
from datetime import datetime

class TodoCreate(BaseModel):
    title: str = Field(..., description="De titel van de todo")

class TodoUpdate(BaseModel):
    done: bool = Field(..., description="De status van de todo")

class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime
