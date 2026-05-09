import uuid
from datetime import datetime, timezone
from typing import List, Optional
from src.models import MovieCreate, MovieResponse
from src.storage import movies_db
from src.service_template.logging_config import get_logger

log = get_logger("logic")

def add_movie(movie_in: MovieCreate) -> MovieResponse:
    movie_id = uuid.uuid4().hex[:8]
    movie = MovieResponse(
        id=movie_id,
        title=movie_in.title,
        genre=movie_in.genre,
        year=movie_in.year,
        added_at=datetime.now(timezone.utc)
    )
    movies_db[movie_id] = movie
    log.info(f"Added movie {movie_id}: {movie.title}")
    return movie

def get_all_movies(genre: Optional[str] = None, year: Optional[int] = None) -> List[MovieResponse]:
    result = list(movies_db.values())
    if genre:
        result = [m for m in result if m.genre.lower() == genre.lower()]
    if year is not None:
        result = [m for m in result if m.year == year]
    log.info(f"Retrieved {len(result)} movies (filters - genre: {genre}, year: {year})")
    return result

def get_movie_by_id(movie_id: str) -> Optional[MovieResponse]:
    movie = movies_db.get(movie_id)
    if movie:
        log.info(f"Found movie {movie_id}")
    else:
        log.info(f"Movie {movie_id} not found")
    return movie
