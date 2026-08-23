from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ExpandRequest(BaseModel):
    rrule: str
    dtstart: str
    tzid: Optional[str] = None
    max_results: Optional[int] = 10000
    after: Optional[str] = None
    before: Optional[str] = None
    inclusive: bool = True

class ExpandResponse(BaseModel):
    rrule: str
    dtstart: str
    tzid: Optional[str] = None
    count: int
    truncated: bool
    terminated_by: Optional[str] = None
    occurrences: List[str]

class NextRequest(BaseModel):
    rrule: str
    dtstart: str
    from_datetime: Optional[str] = None
    n: int = 1
    inclusive: bool = True

class NextResponse(BaseModel):
    rrule: str
    from_datetime: str
    n: int
    occurrences: List[str]
    exhausted: bool

class ValidateRequest(BaseModel):
    rrule: str
    dtstart: str

class ValidateResponse(BaseModel):
    valid: bool
    normalized: Optional[str] = None
    parts: Optional[Dict[str, Any]] = None
    infinite: Optional[bool] = None
    errors: List[str] = []
    warnings: List[str] = []

class DescribeRequest(BaseModel):
    rrule: str
    dtstart: str
    locale: str = "en"

class DescribeResponse(BaseModel):
    rrule: str
    locale: str
    text: str
    infinite: bool
    terminated_by: Optional[str] = None

class RecurrenceSetRequest(BaseModel):
    dtstart: str
    rrules: List[str] = []
    rdates: List[str] = []
    exdates: List[str] = []
    max_results: Optional[int] = 10000

class RecurrenceSetResponse(BaseModel):
    count: int
    truncated: bool
    occurrences: List[str]
    excluded: List[str]

class BatchItem(BaseModel):
    id: str
    rrule: str
    dtstart: str

class BatchRequest(BaseModel):
    items: List[BatchItem]
    max_results: Optional[int] = 10000

class BatchResult(BaseModel):
    id: str
    ok: bool
    count: Optional[int] = None
    occurrences: Optional[List[str]] = None
    error: Optional[Dict[str, str]] = None

class BatchResponse(BaseModel):
    results: List[BatchResult]

class StatusResponse(BaseModel):
    status: str
    version: str
    rfc: str
    supported_parts: List[str]
    limits: Dict[str, int]
