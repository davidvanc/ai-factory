from typing import List
from pydantic import BaseModel, Field, StrictStr

class ReverseRequest(BaseModel):
    text: StrictStr = Field(
        ..., 
        max_length=10000, 
        description="The string to reverse"
    )
    unicode_safe: bool = Field(
        False, 
        description="If true, reverses by grapheme clusters to keep emojis and diacritics intact"
    )

class ReverseResponse(BaseModel):
    original: str
    reversed: str
    length: int
    unicode_safe: bool

class BatchReverseRequest(BaseModel):
    items: List[StrictStr] = Field(
        ..., 
        max_length=1000, 
        description="List of strings to reverse (max 1000 items)"
    )
    unicode_safe: bool = Field(
        False, 
        description="If true, reverses by grapheme clusters"
    )

class BatchReverseItem(BaseModel):
    original: str
    reversed: str
    length: int

class BatchReverseResponse(BaseModel):
    results: List[BatchReverseItem]
    count: int
    unicode_safe: bool

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
