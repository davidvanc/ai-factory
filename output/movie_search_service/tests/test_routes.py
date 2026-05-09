import pytest
from src.storage import clear_db
from src.logic import add_movie, get_all_movies, get_movie_by_id
from src.models import MovieCreate

@pytest.fixture(autouse=True)
def setup_teardown():
    clear_db()
    yield
    clear_db()

# --- Integration Tests ---

def test_post_movies_creates_movie(client):
    response = client.post("/movies", json={"title": "Mad Max", "genre": "action", "year": 2015})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "added_at" in data
    assert data["title"] == "Mad Max"
    assert data["genre"] == "action"
    assert data["year"] == 2015

def test_post_movies_missing_fields(client):
    response = client.post("/movies", json={"title": "Mad Max"})
    assert response.status_code == 422

def test_post_movies_invalid_year(client):
    response = client.post("/movies", json={"title": "Mad Max", "genre": "action", "year": "not-an-int"})
    assert response.status_code == 422

def test_get_movies_returns_all(client):
    client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    client.post("/movies", json={"title": "Movie 2", "genre": "comedy", "year": 2021})
    
    response = client.get("/movies")
    assert response.status_code == 200
    data = response.json()
    assert len(data["movies"]) == 2

def test_get_movies_filter_by_genre(client):
    client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    client.post("/movies", json={"title": "Movie 2", "genre": "comedy", "year": 2021})
    
    response = client.get("/movies?genre=action")
    assert response.status_code == 200
    data = response.json()
    assert len(data["movies"]) == 1
    assert data["movies"][0]["genre"] == "action"

def test_get_movies_filter_by_year(client):
    client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    client.post("/movies", json={"title": "Movie 2", "genre": "comedy", "year": 2021})
    
    response = client.get("/movies?year=2020")
    assert response.status_code == 200
    data = response.json()
    assert len(data["movies"]) == 1
    assert data["movies"][0]["year"] == 2020

def test_get_movies_filter_by_genre_and_year(client):
    client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    client.post("/movies", json={"title": "Movie 2", "genre": "action", "year": 2021})
    client.post("/movies", json={"title": "Movie 3", "genre": "comedy", "year": 2020})
    
    response = client.get("/movies?genre=action&year=2020")
    assert response.status_code == 200
    data = response.json()
    assert len(data["movies"]) == 1
    assert data["movies"][0]["title"] == "Movie 1"

def test_get_movie_by_id(client):
    post_resp = client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    movie_id = post_resp.json()["id"]
    
    response = client.get(f"/movies/{movie_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == movie_id
    assert data["title"] == "Movie 1"

def test_get_movie_by_id_not_found(client):
    response = client.get("/movies/nonexistent")
    assert response.status_code == 404

def test_get_movies_empty_list_on_no_match(client):
    client.post("/movies", json={"title": "Movie 1", "genre": "action", "year": 2020})
    
    response = client.get("/movies?genre=horror")
    assert response.status_code == 200
    data = response.json()
    assert data["movies"] == []

# --- Unit Tests ---

def test_logic_add_movie():
    movie_in = MovieCreate(title="Test", genre="TestGenre", year=2000)
    movie = add_movie(movie_in)
    assert movie.title == "Test"
    assert movie.id is not None

def test_logic_get_all_movies():
    movie_in = MovieCreate(title="Test2", genre="TestGenre", year=2000)
    add_movie(movie_in)
    movies = get_all_movies()
    assert len(movies) == 1

def test_logic_get_movie_by_id():
    movie_in = MovieCreate(title="Test3", genre="TestGenre", year=2000)
    movie = add_movie(movie_in)
    fetched = get_movie_by_id(movie.id)
    assert fetched is not None
    assert fetched.id == movie.id

def test_logic_get_movie_by_id_not_found():
    fetched = get_movie_by_id("invalid_id")
    assert fetched is None
