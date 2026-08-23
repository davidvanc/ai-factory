from dateutil.rrule import rrulestr
from dateutil.parser import parse as parse_date
from dateutil.tz import gettz, tzutc
import datetime
from typing import List, Optional, Tuple

def expand_rrule(rrule_str: str, dtstart_str: str, tzid: Optional[str] = None, max_results: int = 10000, after: Optional[str] = None, before: Optional[str] = None) -> Tuple[List[datetime.datetime], bool, bool]:
    try:
        dtstart = parse_date(dtstart_str)
    except Exception:
        raise ValueError("Invalid dtstart")

    is_date_only = len(dtstart_str) <= 10

    if tzid:
        tz = gettz(tzid)
        if not tz:
            raise ValueError("Invalid TZID")
        if not is_date_only:
            dtstart = dtstart.replace(tzinfo=tz)
    elif not is_date_only and dtstart.tzinfo is None:
        if dtstart_str.endswith('Z'):
            dtstart = dtstart.replace(tzinfo=tzutc())

    try:
        rule = rrulestr(rrule_str, dtstart=dtstart)
    except Exception as e:
        raise ValueError(f"Invalid RRULE: {str(e)}")

    occurrences = []
    truncated = False
    
    after_dt = parse_date(after).replace(tzinfo=dtstart.tzinfo) if after else None
    before_dt = parse_date(before).replace(tzinfo=dtstart.tzinfo) if before else None

    for i, dt in enumerate(rule):
        if before_dt and dt > before_dt:
            break
        if after_dt and dt < after_dt:
            continue
            
        if len(occurrences) >= max_results:
            truncated = True
            break
        occurrences.append(dt)
        
    return occurrences, truncated, is_date_only

def format_dt(dt: datetime.datetime, is_date_only: bool) -> str:
    if is_date_only:
        return dt.strftime("%Y-%m-%d")
    if dt.tzinfo:
        return dt.isoformat()
    return dt.isoformat()
