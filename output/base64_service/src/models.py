from typing import List, Optional
from pydantic import BaseModel, Field, StrictBool, StrictStr


class EncodeRequest(BaseModel):
    text: StrictStr = Field(..., description="Tekst die naar base64 geencodeerd wordt")
    url_safe: StrictBool = False
    strip_padding: StrictBool = False


class EncodeResponse(BaseModel):
    input_text: str
    encoded: str
    alphabet: str
    input_bytes: int
    output_length: int


class DecodeRequest(BaseModel):
    data: StrictStr = Field(...)
    url_safe: StrictBool = False
    fix_padding: StrictBool = True


class DecodeResponse(BaseModel):
    input_data: str
    decoded: str
    alphabet: str
    padding_fixed: bool
    output_length: int


class ValidateRequest(BaseModel):
    data: StrictStr = Field(...)


class ValidateResponse(BaseModel):
    data: str
    valid: bool
    reason: Optional[str] = None
    error_code: Optional[str] = None


class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    supported_alphabets: List[str]


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: str
