from pydantic import BaseModel, field_validator
from datetime import date
import re

class DayOfWeekRequest(BaseModel):
    date: date

    @field_validator('date', mode='before')
    @classmethod
    def check_date_format(cls, v):
        if isinstance(v, str):
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

class DayOfWeekResponse(BaseModel):
    date: str
    day_of_week: str
