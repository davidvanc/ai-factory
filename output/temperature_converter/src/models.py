from pydantic import BaseModel, Field, field_validator

class TemperatureRequest(BaseModel):
    value: float

class ConversionRequest(BaseModel):
    value: float
    from_unit: str = Field(..., description="Unit to convert from (C or F)")
    to_unit: str = Field(..., description="Unit to convert to (C or F)")

    @field_validator('from_unit', 'to_unit')
    @classmethod
    def validate_units(cls, v: str) -> str:
        if v not in ['C', 'F']:
            raise ValueError("Unit must be 'C' or 'F'")
        return v

class ConversionResponse(BaseModel):
    input: float
    input_unit: str
    output: float
    output_unit: str

class StatusResponse(BaseModel):
    status: str
    service: str
