from fastapi import APIRouter, HTTPException
from typing import List
from src.models import PostCreate, PostResponse, CommentCreate, CommentResponse
from src.logic import create_post, get_all_posts, get_post, create_comment, get_comments
from src.service_template.logging_config import get_logger

log = get_logger("blog_routes")
router = APIRouter()

@router.post("/posts", response_model=PostResponse)
def api_create_post(post: PostCreate):
    log.info(f"Creating post with title: {post.title}")
    return create_post(post)

@router.get("/posts", response_model=List[PostResponse])
def api_get_posts():
    log.info("Fetching all posts")
    return get_all_posts()

@router.get("/posts/{id}", response_model=PostResponse)
def api_get_post(id: int):
    log.info(f"Fetching post {id}")
    post = get_post(id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/posts/{id}/comments", response_model=CommentResponse)
def api_create_comment(id: int, comment: CommentCreate):
    log.info(f"Creating comment for post {id}")
    new_comment = create_comment(id, comment)
    if not new_comment:
        raise HTTPException(status_code=404, detail="Post not found")
    return new_comment

@router.get("/posts/{id}/comments", response_model=List[CommentResponse])
def api_get_comments(id: int):
    log.info(f"Fetching comments for post {id}")
    comments = get_comments(id)
    if comments is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return comments
