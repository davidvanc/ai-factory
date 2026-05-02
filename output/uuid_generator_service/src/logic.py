import uuid
from typing import List

def generate_uuid() -> str:
    return str(uuid.uuid4())

def generate_uuids(count: int) -> List[str]:
    return [str(uuid.uuid4()) for _ in range(count)]
