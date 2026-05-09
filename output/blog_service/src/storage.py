from typing import Dict, List
from src.models import PostResponse, CommentResponse

class Storage:
    def __init__(self):
        self.posts: Dict[int, PostResponse] = {}
        self.comments: Dict[int, List[CommentResponse]] = {}
        self.post_id_counter = 1
        self.comment_id_counter = 1

    def clear(self):
        self.posts.clear()
        self.comments.clear()
        self.post_id_counter = 1
        self.comment_id_counter = 1

storage = Storage()
