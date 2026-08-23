from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, StrictStr
from src import config


class ErrorResponse(BaseModel):
    error_code: StrictStr
    message: StrictStr
    detail: Optional[StrictStr] = None
    position: Optional[StrictInt] = None


class EncodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: StrictStr
    url_safe: StrictBool = False
    encoding: StrictStr = config.DEFAULT_ENCODING


class DecodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: StrictStr
    encoding: StrictStr = config.DEFAULT_ENCODING
    strict: StrictBool = True


class ValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: StrictStr


class EncodeResponse(BaseModel):
    encoded: StrictStr
    input_bytes: StrictInt
    output_length: StrictInt
    url_safe: StrictBool
    encoding: StrictStr


class DecodeResponse(BaseModel):
    decoded: StrictStr
    input_length: StrictInt
    output_bytes: StrictInt
    encoding: StrictStr
    detected_alphabet: StrictStr


class ValidateResponse(BaseModel):
    valid: StrictBool
    error_code: Optional[StrictStr] = None
    message: Optional[StrictStr] = None
    position: Optional[StrictInt] = None
    detected_alphabet: Optional[StrictStr] = None


class StatusResponse(BaseModel):
    status: StrictStr
    service: StrictStr
    version: StrictStr
    supported_alphabets: List[StrictStr]
    max_input_bytes: StrictInt
    counters: Dict[str, StrictInt]
