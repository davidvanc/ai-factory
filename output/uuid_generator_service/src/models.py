from pydantic import BaseModel, Field
from typing import List

class GenerateResponse(BaseModel):
    uuid: str

class GenerateBatchRequest(BaseModel):
    count: int = Field(..., ge=1, le=1000)

class GenerateBatchResponse(BaseModel):
    uuids: List[str]
    count: int
