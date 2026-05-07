from pydantic import BaseModel, Field

class ToRomanRequest(BaseModel):
    number: int = Field(..., ge=1, le=3999, description="Integer between 1 and 3999")

class ToRomanResponse(BaseModel):
    number: int
    roman: str

class ToIntegerRequest(BaseModel):
    roman: str = Field(..., min_length=1, description="Canonical Roman numeral string")

class ToIntegerResponse(BaseModel):
    roman: str
    number: int

class ConvertResponse(BaseModel):
    number: int
    roman: str

class StatusResponse(BaseModel):
    status: str
    min: int
    max: int
