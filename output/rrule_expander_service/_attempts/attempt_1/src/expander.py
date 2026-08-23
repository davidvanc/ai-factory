from dateutil.rrule import rrulestr, rruleset
from dateutil import tz
from datetime import datetime, date, time
from typing import Union, List, Tuple
import re

def expand(rrule_str: str, dtstart: Union[datetime, date], tzid: str = None, max_results: int = 1000, after: Union[datetime, date] = None, before: Union[datetime, date] = None, inclusive: bool = True):
    is_date_only = not isinstance(dtstart, datetime)
    
    tzinfo = None
    if tzid:
        tzinfo = tz.gettz(tzid)
        if not tzinfo:
            raise ValueError(f"Invalid TZID: {tzid}")
            
    if is_date_only:
        dtstart_naive = datetime.combine(dtstart, time(0, 0))
    else:
        if dtstart.tzinfo is not None:
            if tzinfo:
                dtstart_aware = dtstart.astimezone(tzinfo)
            else:
                dtstart_aware = dtstart
                tzinfo = dtstart.tzinfo
            dtstart_naive = dtstart_aware.replace(tzinfo=None)
        else:
            dtstart_naive = dtstart
            
    match = re.search(r'UNTIL=([0-9T]+Z)', rrule_str.upper())
    if match:
        until_str = match.group(1)
        until_dt = datetime.strptime(until_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=tz.UTC)
        if tzinfo:
            until_local = until_dt.astimezone(tzinfo).replace(tzinfo=None)
        else:
            until_local = until_dt.replace(tzinfo=None)
        local_until_str = until_local.strftime("%Y%m%dT%H%M%S")
        rrule_str = re.sub(r'UNTIL=[0-9T]+Z', f'UNTIL={local_until_str}', rrule_str, flags=re.IGNORECASE)
        
    try:
        rule = rrulestr(rrule_str, dtstart=dtstart_naive)
    except Exception as e:
        raise ValueError(f"Invalid RRULE: {e}")
        
    occurrences = []
    count = 0
    truncated = False
    
    after_naive = None
    if after:
        if isinstance(after, datetime) and after.tzinfo:
            after_naive = after.astimezone(tzinfo or tz.UTC).replace(tzinfo=None)
        elif isinstance(after, datetime):
            after_naive = after
        else:
            after_naive = datetime.combine(after, time(0, 0))
            
    before_naive = None
    if before:
        if isinstance(before, datetime) and before.tzinfo:
            before_naive = before.astimezone(tzinfo or tz.UTC).replace(tzinfo=None)
        elif isinstance(before, datetime):
            before_naive = before
        else:
            before_naive = datetime.combine(before, time(23, 59, 59))

    for dt in rule:
        if before_naive:
            if inclusive and dt > before_naive:
                break
            if not inclusive and dt >= before_naive:
                break
                
        if after_naive:
            if inclusive and dt < after_naive:
                continue
            if not inclusive and dt <= after_naive:
                continue
                
        if count >= max_results:
            truncated = True
            break
            
        if is_date_only:
            occurrences.append(dt.date())
        else:
            if tzinfo:
                occurrences.append(dt.replace(tzinfo=tzinfo))
            else:
                occurrences.append(dt)
        count += 1
        
    return occurrences, truncated

def expand_recurrence_set(rrules: List[str], rdates: List[Union[datetime, date]], exdates: List[Union[datetime, date]], dtstart: Union[datetime, date], tzid: str = None, max_results: int = 1000):
    is_date_only = not isinstance(dtstart, datetime)
    
    tzinfo = None
    if tzid:
        tzinfo = tz.gettz(tzid)
        if not tzinfo:
            raise ValueError(f"Invalid TZID: {tzid}")
            
    def to_naive(dt):
        if not isinstance(dt, datetime):
            return datetime.combine(dt, time(0, 0))
        if dt.tzinfo:
            if tzinfo:
                return dt.astimezone(tzinfo).replace(tzinfo=None)
            return dt.replace(tzinfo=None)
        return dt

    dtstart_naive = to_naive(dtstart)
    rset = rruleset()
    
    for rrule_str in rrules:
        match = re.search(r'UNTIL=([0-9T]+Z)', rrule_str.upper())
        if match:
            until_str = match.group(1)
            until_dt = datetime.strptime(until_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=tz.UTC)
            if tzinfo:
                until_local = until_dt.astimezone(tzinfo).replace(tzinfo=None)
            else:
                until_local = until_dt.replace(tzinfo=None)
            local_until_str = until_local.strftime("%Y%m%dT%H%M%S")
            rrule_str = re.sub(r'UNTIL=[0-9T]+Z', f'UNTIL={local_until_str}', rrule_str, flags=re.IGNORECASE)
            
        rule = rrulestr(rrule_str, dtstart=dtstart_naive)
        rset.rrule(rule)
        
    for rd in rdates:
        rset.rdate(to_naive(rd))
        
    excluded_naive = set()
    for ex in exdates:
        en = to_naive(ex)
        rset.exdate(en)
        excluded_naive.add(en)
        
    occurrences = []
    count = 0
    truncated = False
    
    for dt in rset:
        if count >= max_results:
            truncated = True
            break
            
        if is_date_only:
            occurrences.append(dt.date())
        else:
            if tzinfo:
                occurrences.append(dt.replace(tzinfo=tzinfo))
            else:
                occurrences.append(dt)
        count += 1
        
    excluded = []
    for en in sorted(list(excluded_naive)):
        if is_date_only:
            excluded.append(en.date())
        else:
            if tzinfo:
                excluded.append(en.replace(tzinfo=tzinfo))
            else:
                excluded.append(en)
                
    return occurrences, excluded, truncated
