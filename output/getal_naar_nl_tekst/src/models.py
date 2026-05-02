from pydantic import BaseModel, field_validator
import re

class ConvertRequest(BaseModel):
    value: str

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: str) -> str:
        if not re.match(r'^-?\d+([.,]\d+)?$', v.strip()):
            raise ValueError("Invalid number format")
        return v.strip()

class ConvertResponse(BaseModel):
    value: str
    text: str
