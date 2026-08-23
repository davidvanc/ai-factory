from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.models import (
    ExpandRequest, ExpandResponse,
    NextRequest, NextResponse,
    ValidateRequest, ValidateResponse,
    DescribeRequest, DescribeResponse,
    RecurrenceSetRequest, RecurrenceSetResponse,
    BatchRequest, BatchResponse,
    StatusResponse
)
from src.logic import (
    do_expand, do_next, do_validate, do_describe, do_recurrence_set_expand, do_batch_expand
)
from src.config import settings

router = APIRouter()

@router.post("/expand", response_model=ExpandResponse)
def expand_post(req: ExpandRequest):
    return do_expand(req)

@router.get("/expand", response_model=ExpandResponse)
def expand_get(
    rrule: str,
    dtstart: str,
    tzid: Optional[str] = None,
    max_results: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    inclusive: bool = True
):
    req = ExpandRequest(
        rrule=rrule,
        dtstart=dtstart,
        tzid=tzid,
        max_results=max_results or settings.max_results,
        after=after,
        before=before,
        inclusive=inclusive
    )
    return do_expand(req)

@router.post("/next", response_model=NextResponse)
def next_post(req: NextRequest):
    return do_next(req)

@router.post("/validate", response_model=ValidateResponse)
def validate_post(req: ValidateRequest):
    return do_validate(req)

@router.post("/describe", response_model=DescribeResponse)
def describe_post(req: DescribeRequest):
    return do_describe(req)

@router.post("/recurrence-set/expand", response_model=RecurrenceSetResponse)
def recurrence_set_expand_post(req: RecurrenceSetRequest):
    return do_recurrence_set_expand(req)

@router.post("/expand/batch", response_model=BatchResponse)
def expand_batch_post(req: BatchRequest):
    return do_batch_expand(req)

@router.get("/status", response_model=StatusResponse)
def status_get():
    return StatusResponse(
        status="ok",
        version="1.0.0",
        rfc="RFC 5545",
        supported_parts=["FREQ", "INTERVAL", "BYDAY", "BYMONTHDAY", "BYMONTH", "BYSETPOS", "WKST", "COUNT", "UNTIL"],
        limits={"max_results": settings.max_results, "max_batch_items": settings.max_batch_items}
    )
