from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="De tekst om te analyseren")

class AnalyzeResponse(BaseModel):
    text: str
    letter_count: int
    word_count: int
    vowel_count: int
    is_palindrome: bool

class HealthResponse(BaseModel):
    status: str
