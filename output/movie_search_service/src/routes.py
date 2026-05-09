from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.models import MovieCreate, MovieResponse, MovieListResponse
from src.logic import add_movie, get_all_movies, get_movie_by_id
from src.service_template.logging_config import get_logger

log = get_logger("routes")
router = APIRouter()

@router.post("/movies", response_model=MovieResponse)
def create_movie(movie: MovieCreate):
    log.info(f"Received request to create movie: {movie.title}")
    return add_movie(movie)

@router.get("/movies", response_model=MovieListResponse)
def list_movies(
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year: Optional[int] = Query(None, description="Filter by year")
):
    log.info(f"Received request to list movies with genre={genre}, year={year}")
    movies = get_all_movies(genre=genre, year=year)
    return MovieListResponse(movies=movies)

@router.get("/movies/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str):
    log.info(f"Received request to get movie {movie_id}")
    movie = get_movie_by_id(movie_id)
    if not movie:
        log.warning(f"Movie {movie_id} not found")
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
