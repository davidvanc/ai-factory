import re
from pydantic import BaseModel, Field, field_validator

class RGB(BaseModel):
    r: int
    g: int
    b: int

class HSL(BaseModel):
    h: float
    s: float
    l: float

class ConvertRequest(BaseModel):
    hex: str = Field(..., description="HEX color code")

    @field_validator('hex')
    @classmethod
    def validate_hex(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', v):
            raise ValueError('Invalid HEX color code')
        return v

class ConvertResponse(BaseModel):
    hex: str
    rgb: RGB
    hsl: HSL
