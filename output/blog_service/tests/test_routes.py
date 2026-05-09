import pytest
from src.storage import storage

@pytest.fixture(autouse=True)
def reset_storage():
    storage.clear()

def test_create_post(client):
    response = client.post("/posts", json={"title": "Hello World", "body": "This is my first post"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Hello World"
    assert data["body"] == "This is my first post"
    assert "created_at" in data

def test_create_post_missing_fields(client):
    response = client.post("/posts", json={"title": "Hello World"})
    assert response.status_code == 422

def test_get_all_posts(client):
    client.post("/posts", json={"title": "Post 1", "body": "Body 1"})
    client.post("/posts", json={"title": "Post 2", "body": "Body 2"})
    response = client.get("/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Post 1"
    assert data[1]["title"] == "Post 2"

def test_get_post_by_id(client):
    post_res = client.post("/posts", json={"title": "Post 1", "body": "Body 1"})
    post_id = post_res.json()["id"]
    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Post 1"

def test_get_post_not_found(client):
    response = client.get("/posts/999")
    assert response.status_code == 404

def test_create_comment(client):
    post_res = client.post("/posts", json={"title": "Post 1", "body": "Body 1"})
    post_id = post_res.json()["id"]
    response = client.post(f"/posts/{post_id}/comments", json={"text": "Great post!"})
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == post_id
    assert data["text"] == "Great post!"
    assert "created_at" in data

def test_create_comment_post_not_found(client):
    response = client.post("/posts/999/comments", json={"text": "Great post!"})
    assert response.status_code == 404

def test_create_comment_missing_text(client):
    post_res = client.post("/posts", json={"title": "Post 1", "body": "Body 1"})
    post_id = post_res.json()["id"]
    response = client.post(f"/posts/{post_id}/comments", json={})
    assert response.status_code == 422

def test_get_comments(client):
    post_res = client.post("/posts", json={"title": "Post 1", "body": "Body 1"})
    post_id = post_res.json()["id"]
    client.post(f"/posts/{post_id}/comments", json={"text": "Comment 1"})
    client.post(f"/posts/{post_id}/comments", json={"text": "Comment 2"})
    
    response = client.get(f"/posts/{post_id}/comments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["text"] == "Comment 1"
    assert data[1]["text"] == "Comment 2"

def test_get_comments_post_not_found(client):
    response = client.get("/posts/999/comments")
    assert response.status_code == 404

def test_logic_create_post():
    from src.logic import create_post
    from src.models import PostCreate
    post = create_post(PostCreate(title="Logic Title", body="Logic Body"))
    assert post.title == "Logic Title"
    assert post.body == "Logic Body"
    assert post.id > 0
