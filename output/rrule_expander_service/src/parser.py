import re
from typing import Tuple, Dict, Any, List

def parse_rrule_string(rrule_str: str) -> Tuple[Dict[str, Any], List[str]]:
    errors = []
    if rrule_str.lower().startswith("rrule:"):
        rrule_str = rrule_str[6:]
    
    parts = {}
    for part in rrule_str.split(";"):
        if not part:
            continue
        if "=" not in part:
            errors.append(f"Invalid part: {part}")
            continue
        k, v = part.split("=", 1)
        k = k.upper()
        v = v.upper()
        
        if k == "FREQ":
            if v not in ["SECONDLY", "MINUTELY", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
                errors.append(f"FREQ={v} is not a valid RFC 5545 frequency")
            parts[k] = v
        elif k == "INTERVAL":
            try:
                val = int(v)
                if val <= 0:
                    errors.append("INTERVAL must be > 0")
                parts[k] = val
            except ValueError:
                errors.append("INTERVAL must be an integer")
        elif k == "COUNT":
            try:
                parts[k] = int(v)
            except ValueError:
                errors.append("COUNT must be an integer")
        elif k == "UNTIL":
            parts[k] = v
        elif k == "BYDAY":
            days = v.split(",")
            parsed_days = []
            for d in days:
                m = re.match(r"([+-]?\d+)?([A-Z]{2})", d)
                if m:
                    ord_val = int(m.group(1)) if m.group(1) else None
                    parsed_days.append({"ordinal": ord_val, "weekday": m.group(2)})
                else:
                    errors.append(f"Invalid BYDAY: {d}")
            parts[k] = parsed_days
        elif k == "BYMONTHDAY":
            try:
                parts[k] = [int(x) for x in v.split(",")]
            except ValueError:
                errors.append("BYMONTHDAY must be integers")
        elif k == "BYMONTH":
            try:
                parts[k] = [int(x) for x in v.split(",")]
            except ValueError:
                errors.append("BYMONTH must be integers")
        elif k == "BYSETPOS":
            try:
                parts[k] = [int(x) for x in v.split(",")]
            except ValueError:
                errors.append("BYSETPOS must be integers")
        elif k == "WKST":
            parts[k] = v
        else:
            parts[k] = v

    if "FREQ" not in parts:
        errors.append("Missing FREQ")
        
    if "COUNT" in parts and "UNTIL" in parts:
        errors.append("COUNT and UNTIL are mutually exclusive")
        
    if parts.get("FREQ") == "WEEKLY" and "BYDAY" in parts:
        for d in parts["BYDAY"]:
            if d.get("ordinal") is not None:
                errors.append("BYDAY with ordinal is invalid for FREQ=WEEKLY")
                
    return parts, errors

def normalize_rrule(parts: Dict[str, Any]) -> str:
    res = []
    for k in ["FREQ", "INTERVAL", "BYMONTH", "BYMONTHDAY", "BYDAY", "BYSETPOS", "WKST", "COUNT", "UNTIL"]:
        if k in parts:
            v = parts[k]
            if k == "BYDAY":
                v_str = ",".join([f"{d['ordinal'] if d['ordinal'] else ''}{d['weekday']}" for d in v])
                res.append(f"{k}={v_str}")
            elif isinstance(v, list):
                res.append(f"{k}={','.join(map(str, v))}")
            else:
                res.append(f"{k}={v}")
    return ";".join(res)
