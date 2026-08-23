import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, date

def parse_rrule_string(rrule_str: str) -> Tuple[Dict[str, Any], List[str]]:
    errors = []
    if rrule_str.upper().startswith("RRULE:"):
        rrule_str = rrule_str[6:]
    
    parts = {}
    for param in rrule_str.split(';'):
        param = param.strip()
        if not param:
            continue
        if '=' not in param:
            errors.append(f"Invalid parameter format: {param}")
            continue
        key, val = param.split('=', 1)
        key = key.upper()
        val = val.upper()
        parts[key] = val
        
    if 'FREQ' not in parts:
        errors.append("Missing required FREQ parameter")
    elif parts['FREQ'] not in ['SECONDLY', 'MINUTELY', 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']:
        errors.append(f"FREQ={parts['FREQ']} is not a valid RFC 5545 frequency")
        
    if 'INTERVAL' in parts:
        try:
            interval = int(parts['INTERVAL'])
            if interval <= 0:
                errors.append("INTERVAL must be a positive integer")
            parts['INTERVAL'] = interval
        except ValueError:
            errors.append("INTERVAL must be an integer")
    else:
        parts['INTERVAL'] = 1
            
    if 'COUNT' in parts:
        try:
            parts['COUNT'] = int(parts['COUNT'])
        except ValueError:
            errors.append("COUNT must be an integer")
            
    if 'BYDAY' in parts:
        byday_list = parts['BYDAY'].split(',')
        parsed_byday = []
        for bd in byday_list:
            match = re.match(r'^([+-]?\d+)?(SU|MO|TU|WE|TH|FR|SA)$', bd)
            if not match:
                errors.append(f"Invalid BYDAY value: {bd}")
                continue
            ord_val, weekday = match.groups()
            if ord_val:
                parsed_byday.append({"ordinal": int(ord_val), "weekday": weekday})
            else:
                parsed_byday.append({"weekday": weekday})
        parts['BYDAY'] = parsed_byday
        
    if 'BYMONTHDAY' in parts:
        try:
            parts['BYMONTHDAY'] = [int(x) for x in parts['BYMONTHDAY'].split(',')]
        except ValueError:
            errors.append("BYMONTHDAY must be a comma-separated list of integers")
            
    if 'BYMONTH' in parts:
        try:
            parts['BYMONTH'] = [int(x) for x in parts['BYMONTH'].split(',')]
        except ValueError:
            errors.append("BYMONTH must be a comma-separated list of integers")
            
    if 'BYSETPOS' in parts:
        try:
            parts['BYSETPOS'] = [int(x) for x in parts['BYSETPOS'].split(',')]
        except ValueError:
            errors.append("BYSETPOS must be a comma-separated list of integers")
            
    return parts, errors

def normalize_rrule(parts: Dict[str, Any]) -> str:
    res = []
    if 'FREQ' in parts:
        res.append(f"FREQ={parts['FREQ']}")
    if parts.get('INTERVAL', 1) > 1:
        res.append(f"INTERVAL={parts['INTERVAL']}")
    for key in ['WKST', 'BYMONTH', 'BYMONTHDAY', 'BYDAY', 'BYSETPOS', 'COUNT', 'UNTIL']:
        if key in parts:
            val = parts[key]
            if key == 'BYDAY':
                bd_strs = []
                for bd in val:
                    if 'ordinal' in bd:
                        bd_strs.append(f"{bd['ordinal']}{bd['weekday']}")
                    else:
                        bd_strs.append(bd['weekday'])
                res.append(f"BYDAY={','.join(bd_strs)}")
            elif isinstance(val, list):
                res.append(f"{key}={','.join(map(str, val))}")
            else:
                res.append(f"{key}={val}")
    return ";".join(res)

def validate_rrule(rrule_str: str, dtstart: datetime | date = None):
    parts, errors = parse_rrule_string(rrule_str)
    
    if 'COUNT' in parts and 'UNTIL' in parts:
        errors.append("COUNT and UNTIL cannot both be present")
        
    if parts.get('FREQ') == 'WEEKLY' and 'BYDAY' in parts:
        for bd in parts['BYDAY']:
            if 'ordinal' in bd:
                errors.append("BYDAY with ordinal is not allowed for WEEKLY frequency")
                break
                
    infinite = 'COUNT' not in parts and 'UNTIL' not in parts
    
    return {
        "valid": len(errors) == 0,
        "normalized": normalize_rrule(parts) if len(errors) == 0 else None,
        "parts": parts,
        "infinite": infinite,
        "errors": errors,
        "warnings": []
    }
