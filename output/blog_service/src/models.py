from pydantic import BaseModel, Field
from datetime import datetime

class PostCreate(BaseModel):
    title: str = Field(..., description="Title of the post")
    body: str = Field(..., description="Body of the post")

class PostResponse(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime

class CommentCreate(BaseModel):
    text: str = Field(..., description="Text of the comment")

class CommentResponse(BaseModel):
    id: int
    post_id: int
    text: str
    created_at: datetime
