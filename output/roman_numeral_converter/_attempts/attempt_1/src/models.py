from pydantic import BaseModel, Field
from typing import Union

class ToRomanRequest(BaseModel):
    number: int = Field(..., ge=1, le=3999)

class ToRomanResponse(BaseModel):
    number: int
    roman: str

class ToIntegerRequest(BaseModel):
    roman: str = Field(..., min_length=1)

class ToIntegerResponse(BaseModel):
    roman: str
    number: int

class ConvertResponse(BaseModel):
    input: str
    input_type: str
    output: Union[int, str]
    output_type: str

class StatusResponse(BaseModel):
    status: str
    service: str
    range: str
