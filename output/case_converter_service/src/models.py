from pydantic import BaseModel
from typing import List

class ConvertRequest(BaseModel):
    text: str
    target_case: str

class ConvertResponse(BaseModel):
    original: str
    target_case: str
    result: str

class ConvertAllRequest(BaseModel):
    text: str

class ConvertAllResponse(BaseModel):
    original: str
    upper: str
    lower: str
    title: str
    snake: str
    kebab: str
    camel: str

class CasesResponse(BaseModel):
    supported_cases: List[str]

class StatusResponse(BaseModel):
    status: str
    service: str
