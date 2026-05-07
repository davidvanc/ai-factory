from pydantic import BaseModel, Field
from typing import Optional

class ISBNRequest(BaseModel):
    isbn: str = Field(..., description="The ISBN code to validate")

class ISBNResponse(BaseModel):
    valid: bool
    format: Optional[str] = None
    normalized: str
    input: str
