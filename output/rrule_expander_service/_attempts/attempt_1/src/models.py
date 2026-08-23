from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, date

def parse_date_or_datetime(v):
    if isinstance(v, str):
        if 'T' in v or ':' in v:
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        else:
            return date.fromisoformat(v)
    return v

class ExpandRequest(BaseModel):
    rrule: str
    dtstart: Union[datetime, date]
    tzid: Optional[str] = None
    max_results: Optional[int] = Field(default=1000)
    after: Optional[Union[datetime, date]] = None
    before: Optional[Union[datetime, date]] = None
    inclusive: bool = True

    @field_validator('dtstart', 'after', 'before', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)

class ExpandResponse(BaseModel):
    rrule: str
    dtstart: Union[datetime, date]
    tzid: Optional[str]
    count: int
    truncated: bool
    terminated_by: Optional[str]
    occurrences: List[Union[datetime, date]]

class NextRequest(BaseModel):
    rrule: str
    dtstart: Union[datetime, date]
    from_datetime: Optional[Union[datetime, date]] = None
    n: int = 1
    inclusive: bool = True

    @field_validator('dtstart', 'from_datetime', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)

class NextResponse(BaseModel):
    rrule: str
    from_datetime: Union[datetime, date]
    n: int
    occurrences: List[Union[datetime, date]]
    exhausted: bool

class ValidateRequest(BaseModel):
    rrule: str
    dtstart: Optional[Union[datetime, date]] = None

    @field_validator('dtstart', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)

class ValidateResponse(BaseModel):
    valid: bool
    normalized: Optional[str]
    parts: Dict[str, Any]
    infinite: bool
    errors: List[str]
    warnings: List[str]

class DescribeRequest(BaseModel):
    rrule: str
    dtstart: Optional[Union[datetime, date]] = None
    locale: str = "en"

    @field_validator('dtstart', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)

class DescribeResponse(BaseModel):
    rrule: str
    locale: str
    text: str
    infinite: bool
    terminated_by: Optional[str]

class RecurrenceSetRequest(BaseModel):
    dtstart: Union[datetime, date]
    rrules: List[str] = []
    rdates: List[Union[datetime, date]] = []
    exdates: List[Union[datetime, date]] = []
    tzid: Optional[str] = None
    max_results: Optional[int] = Field(default=1000)

    @field_validator('dtstart', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)
        
    @field_validator('rdates', 'exdates', mode='before')
    def parse_dt_list(cls, v):
        if isinstance(v, list):
            return [parse_date_or_datetime(x) for x in v]
        return v

class RecurrenceSetResponse(BaseModel):
    count: int
    truncated: bool
    occurrences: List[Union[datetime, date]]
    excluded: List[Union[datetime, date]]

class BatchItem(BaseModel):
    id: str
    rrule: str
    dtstart: Union[datetime, date]
    tzid: Optional[str] = None

    @field_validator('dtstart', mode='before')
    def parse_dt(cls, v):
        return parse_date_or_datetime(v)

class BatchRequest(BaseModel):
    items: List[BatchItem]
    max_results: Optional[int] = Field(default=1000)

class BatchItemError(BaseModel):
    code: str
    message: str

class BatchItemResult(BaseModel):
    id: str
    ok: bool
    count: Optional[int] = None
    occurrences: Optional[List[Union[datetime, date]]] = None
    error: Optional[BatchItemError] = None

class BatchResponse(BaseModel):
    results: List[BatchItemResult]

class StatusResponse(BaseModel):
    status: str
    version: str
    rfc: str
    supported_parts: List[str]
    limits: Dict[str, int]
