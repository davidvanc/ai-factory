from pydantic import BaseModel, field_validator
import re

class DayOfWeekRequest(BaseModel):
    date: str

    @field_validator('date')
    @classmethod
    def validate_format(cls, v: str) -> str:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("Invalid date format. Must be YYYY-MM-DD")
        return v

class DayOfWeekResponse(BaseModel):
    day: str
