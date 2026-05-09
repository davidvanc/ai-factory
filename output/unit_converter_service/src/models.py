from pydantic import BaseModel

class ConversionRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str

class ConversionResponse(BaseModel):
    from_unit: str
    to_unit: str
    result: float
