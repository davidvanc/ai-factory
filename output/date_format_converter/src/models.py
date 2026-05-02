from enum import Enum
from pydantic import BaseModel
from typing import List

class DateFormat(str, Enum):
    iso = 'iso'
    eu = 'eu'
    us = 'us'
    unix = 'unix'

class ConvertRequest(BaseModel):
    value: str
    from_format: DateFormat
    to_format: DateFormat

class ConvertResponse(BaseModel):
    original: str
    converted: str
    from_format: DateFormat
    to_format: DateFormat

class DetectRequest(BaseModel):
    value: str

class DetectResponse(BaseModel):
    value: str
    detected_format: DateFormat

class FormatItem(BaseModel):
    key: str
    example: str

class FormatsResponse(BaseModel):
    formats: List[FormatItem]

class StatusResponse(BaseModel):
    status: str
