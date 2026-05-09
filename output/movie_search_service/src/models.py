from pydantic import BaseModel
from datetime import datetime

class MovieCreate(BaseModel):
    title: str
    genre: str
    year: int

class MovieResponse(BaseModel):
    id: str
    title: str
    genre: str
    year: int
    added_at: datetime

class MovieListResponse(BaseModel):
    movies: list[MovieResponse]
