from typing import Dict
from src.models import MovieResponse

# In-memory storage for movies
movies_db: Dict[str, MovieResponse] = {}

def clear_db() -> None:
    """Clears the database, useful for testing."""
    movies_db.clear()
