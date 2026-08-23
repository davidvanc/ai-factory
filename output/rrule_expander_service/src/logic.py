from src.models import (
    ExpandRequest, ExpandResponse,
    NextRequest, NextResponse,
    ValidateRequest, ValidateResponse,
    DescribeRequest, DescribeResponse,
    RecurrenceSetRequest, RecurrenceSetResponse,
    BatchRequest, BatchResponse, BatchResult
)
from src.parser import parse_rrule_string, normalize_rrule
from src.expander import expand_rrule, format_dt
from src.describe import describe_rrule
from src.config import settings
from fastapi import HTTPException
from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc
from dateutil.rrule import rrulestr, rruleset
import datetime

def do_expand(req: ExpandRequest) -> ExpandResponse:
    if req.max_results > settings.max_results:
        raise HTTPException(status_code=422, detail="max_results exceeds server limit")
        
    parts, errors = parse_rrule_string(req.rrule)
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])
        
    try:
        occurrences, truncated, is_date_only = expand_rrule(
            req.rrule, req.dtstart, req.tzid, req.max_results, req.after, req.before
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    formatted = [format_dt(dt, is_date_only) for dt in occurrences]
    
    terminated_by = None
    if "COUNT" in parts:
        terminated_by = "COUNT"
    elif "UNTIL" in parts:
        terminated_by = "UNTIL"
        
    return ExpandResponse(
        rrule=req.rrule,
        dtstart=format_dt(parse_date(req.dtstart), is_date_only) if is_date_only else req.dtstart,
        tzid=req.tzid,
        count=len(formatted),
        truncated=truncated,
        terminated_by=terminated_by,
        occurrences=formatted
    )

def do_next(req: NextRequest) -> NextResponse:
    parts, errors = parse_rrule_string(req.rrule)
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])
        
    try:
        occurrences, _, is_date_only = expand_rrule(req.rrule, req.dtstart, max_results=10000)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    from_dt = parse_date(req.from_datetime or datetime.datetime.now(tzutc()).isoformat())
    if from_dt.tzinfo is None and not is_date_only:
        from_dt = from_dt.replace(tzinfo=tzutc())
        
    res = []
    for dt in occurrences:
        if req.inclusive and dt >= from_dt:
            res.append(dt)
        elif not req.inclusive and dt > from_dt:
            res.append(dt)
        if len(res) == req.n:
            break
            
    exhausted = len(res) < req.n and ("COUNT" in parts or "UNTIL" in parts)
    
    return NextResponse(
        rrule=req.rrule,
        from_datetime=format_dt(from_dt, False),
        n=req.n,
        occurrences=[format_dt(dt, is_date_only) for dt in res],
        exhausted=exhausted
    )

def do_validate(req: ValidateRequest) -> ValidateResponse:
    parts, errors = parse_rrule_string(req.rrule)
    valid = len(errors) == 0
    infinite = "COUNT" not in parts and "UNTIL" not in parts if valid else None
    
    return ValidateResponse(
        valid=valid,
        normalized=normalize_rrule(parts) if valid else None,
        parts=parts if valid else None,
        infinite=infinite,
        errors=errors,
        warnings=[]
    )

def do_describe(req: DescribeRequest) -> DescribeResponse:
    parts, errors = parse_rrule_string(req.rrule)
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])
        
    text = describe_rrule(req.rrule, req.locale)
    infinite = "COUNT" not in parts and "UNTIL" not in parts
    terminated_by = "COUNT" if "COUNT" in parts else ("UNTIL" if "UNTIL" in parts else None)
    
    return DescribeResponse(
        rrule=req.rrule,
        locale=req.locale,
        text=text,
        infinite=infinite,
        terminated_by=terminated_by
    )

def do_recurrence_set_expand(req: RecurrenceSetRequest) -> RecurrenceSetResponse:
    try:
        dtstart = parse_date(req.dtstart)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid dtstart")
        
    is_date_only = len(req.dtstart) <= 10
    if not is_date_only and dtstart.tzinfo is None and req.dtstart.endswith('Z'):
        dtstart = dtstart.replace(tzinfo=tzutc())
        
    rset = rruleset()
    
    for r in req.rrules:
        try:
            rule = rrulestr(r, dtstart=dtstart)
            rset.rrule(rule)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
            
    for d in req.rdates:
        try:
            rd = parse_date(d)
            if not is_date_only and rd.tzinfo is None and d.endswith('Z'):
                rd = rd.replace(tzinfo=tzutc())
            rset.rdate(rd)
        except Exception:
            pass
            
    exdates_parsed = []
    for d in req.exdates:
        try:
            ed = parse_date(d)
            if not is_date_only and ed.tzinfo is None and d.endswith('Z'):
                ed = ed.replace(tzinfo=tzutc())
            rset.exdate(ed)
            exdates_parsed.append(ed)
        except Exception:
            pass
            
    occurrences = []
    truncated = False
    max_res = req.max_results or settings.max_results
    
    for i, dt in enumerate(rset):
        if i >= max_res:
            truncated = True
            break
        occurrences.append(dt)
        
    return RecurrenceSetResponse(
        count=len(occurrences),
        truncated=truncated,
        occurrences=[format_dt(dt, is_date_only) for dt in occurrences],
        excluded=[format_dt(dt, is_date_only) for dt in exdates_parsed]
    )

def do_batch_expand(req: BatchRequest) -> BatchResponse:
    if len(req.items) > settings.max_batch_items:
        raise HTTPException(status_code=422, detail="Too many items")
        
    results = []
    for item in req.items:
        parts, errors = parse_rrule_string(item.rrule)
        if errors:
            results.append(BatchResult(
                id=item.id,
                ok=False,
                error={"code": "INVALID_FREQ" if "FREQ" in errors[0] else "INVALID", "message": errors[0]}
            ))
            continue
            
        try:
            occurrences, _, is_date_only = expand_rrule(item.rrule, item.dtstart, max_results=req.max_results or settings.max_results)
            formatted = [format_dt(dt, is_date_only) for dt in occurrences]
            results.append(BatchResult(
                id=item.id,
                ok=True,
                count=len(formatted),
                occurrences=formatted
            ))
        except Exception as e:
            results.append(BatchResult(
                id=item.id,
                ok=False,
                error={"code": "ERROR", "message": str(e)}
            ))
            
    return BatchResponse(results=results)
