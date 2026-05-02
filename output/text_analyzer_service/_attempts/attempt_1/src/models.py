from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    text: str
    letter_count: int
    word_count: int
    vowel_count: int
    is_palindrome: bool

class StatusResponse(BaseModel):
    status: str
    service: str
