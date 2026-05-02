from pydantic import BaseModel, Field

class ConvertRequest(BaseModel):
    number: int = Field(..., ge=0, le=1000000000000000)

class ConvertResponse(BaseModel):
    number: int
    text: str

class StatusResponse(BaseModel):
    status: str
    range: str

class HealthResponse(BaseModel):
    status: str
