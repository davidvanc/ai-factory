from src.models import (
    ExpandRequest, ExpandResponse,
    NextRequest, NextResponse,
    ValidateRequest, ValidateResponse,
    DescribeRequest, DescribeResponse,
    RecurrenceSetRequest, RecurrenceSetResponse,
    BatchRequest, BatchResponse, BatchItemResult, BatchItemError
)
from src.expander import expand, expand_recurrence_set
from src.parser import validate_rrule
from src.describe import describe_rrule
from src.config import settings
from fastapi import HTTPException
from datetime import datetime, timezone

def do_expand(req: ExpandRequest) -> ExpandResponse:
    if req.max_results > settings.max_results:
        raise HTTPException(status_code=422, detail=f"max_results exceeds server limit of {settings.max_results}")
        
    val = validate_rrule(req.rrule, req.dtstart)
    if not val['valid']:
        raise HTTPException(status_code=422, detail=f"Invalid RRULE: {val['errors']}")
        
    try:
        occurrences, truncated = expand(
            rrule_str=req.rrule,
            dtstart=req.dtstart,
            tzid=req.tzid,
            max_results=req.max_results,
            after=req.after,
            before=req.before,
            inclusive=req.inclusive
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    terminated_by = None
    if 'COUNT' in val['parts']:
        terminated_by = 'COUNT'
    elif 'UNTIL' in val['parts']:
        terminated_by = 'UNTIL'
        
    return ExpandResponse(
        rrule=req.rrule,
        dtstart=req.dtstart,
        tzid=req.tzid,
        count=len(occurrences),
        truncated=truncated,
        terminated_by=terminated_by,
        occurrences=occurrences
    )

def do_next(req: NextRequest) -> NextResponse:
    val = validate_rrule(req.rrule, req.dtstart)
    if not val['valid']:
        raise HTTPException(status_code=422, detail=f"Invalid RRULE: {val['errors']}")
        
    from_dt = req.from_datetime or datetime.now(timezone.utc)
    
    try:
        occurrences, truncated = expand(
            rrule_str=req.rrule,
            dtstart=req.dtstart,
            tzid=None,
            max_results=req.n,
            after=from_dt,
            inclusive=req.inclusive
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    exhausted = False
    if len(occurrences) < req.n:
        exhausted = True
    elif len(occurrences) > 0:
        more, _ = expand(
            rrule_str=req.rrule,
            dtstart=req.dtstart,
            tzid=None,
            max_results=1,
            after=occurrences[-1],
            inclusive=False
        )
        if not more:
            exhausted = True
            
    return NextResponse(
        rrule=req.rrule,
        from_datetime=from_dt,
        n=req.n,
        occurrences=occurrences,
        exhausted=exhausted
    )

def do_validate(req: ValidateRequest) -> ValidateResponse:
    val = validate_rrule(req.rrule, req.dtstart)
    return ValidateResponse(**val)

def do_describe(req: DescribeRequest) -> DescribeResponse:
    val = validate_rrule(req.rrule, req.dtstart)
    text = describe_rrule(req.rrule, req.locale)
    
    terminated_by = None
    if 'COUNT' in val['parts']:
        terminated_by = 'COUNT'
    elif 'UNTIL' in val['parts']:
        terminated_by = 'UNTIL'
        
    return DescribeResponse(
        rrule=req.rrule,
        locale=req.locale,
        text=text,
        infinite=val['infinite'],
        terminated_by=terminated_by
    )

def do_recurrence_set_expand(req: RecurrenceSetRequest) -> RecurrenceSetResponse:
    if req.max_results > settings.max_results:
        raise HTTPException(status_code=422, detail="max_results exceeds server limit")
        
    try:
        occurrences, excluded, truncated = expand_recurrence_set(
            rrules=req.rrules,
            rdates=req.rdates,
            exdates=req.exdates,
            dtstart=req.dtstart,
            tzid=req.tzid,
            max_results=req.max_results
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    return RecurrenceSetResponse(
        count=len(occurrences),
        truncated=truncated,
        occurrences=occurrences,
        excluded=excluded
    )

def do_batch_expand(req: BatchRequest) -> BatchResponse:
    if len(req.items) > settings.max_batch_items:
        raise HTTPException(status_code=422, detail="Too many items in batch")
        
    results = []
    for item in req.items:
        val = validate_rrule(item.rrule, item.dtstart)
        if not val['valid']:
            results.append(BatchItemResult(
                id=item.id,
                ok=False,
                error=BatchItemError(code="INVALID_RRULE", message=val['errors'][0])
            ))
            continue
            
        try:
            occurrences, _ = expand(
                rrule_str=item.rrule,
                dtstart=item.dtstart,
                tzid=item.tzid,
                max_results=req.max_results
            )
            results.append(BatchItemResult(
                id=item.id,
                ok=True,
                count=len(occurrences),
                occurrences=occurrences
            ))
        except Exception as e:
            results.append(BatchItemResult(
                id=item.id,
                ok=False,
                error=BatchItemError(code="EXPAND_ERROR", message=str(e))
            ))
            
    return BatchResponse(results=results)
