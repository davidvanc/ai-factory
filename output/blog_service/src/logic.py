from datetime import datetime, timezone
from typing import List, Optional
from src.models import PostCreate, PostResponse, CommentCreate, CommentResponse
from src.storage import storage

def create_post(post_in: PostCreate) -> PostResponse:
    post_id = storage.post_id_counter
    storage.post_id_counter += 1
    post = PostResponse(
        id=post_id,
        title=post_in.title,
        body=post_in.body,
        created_at=datetime.now(timezone.utc)
    )
    storage.posts[post_id] = post
    storage.comments[post_id] = []
    return post

def get_all_posts() -> List[PostResponse]:
    return list(storage.posts.values())

def get_post(post_id: int) -> Optional[PostResponse]:
    return storage.posts.get(post_id)

def create_comment(post_id: int, comment_in: CommentCreate) -> Optional[CommentResponse]:
    if post_id not in storage.posts:
        return None
    
    comment_id = storage.comment_id_counter
    storage.comment_id_counter += 1
    comment = CommentResponse(
        id=comment_id,
        post_id=post_id,
        text=comment_in.text,
        created_at=datetime.now(timezone.utc)
    )
    storage.comments[post_id].append(comment)
    return comment

def get_comments(post_id: int) -> Optional[List[CommentResponse]]:
    if post_id not in storage.posts:
        return None
    return storage.comments.get(post_id, [])
