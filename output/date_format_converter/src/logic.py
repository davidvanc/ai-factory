from datetime import datetime, timezone

def parse_date(value: str, fmt: str) -> datetime:
    if fmt == 'iso':
        dt = datetime.strptime(value, "%Y-%m-%d")
    elif fmt == 'eu':
        dt = datetime.strptime(value, "%d-%m-%Y")
    elif fmt == 'us':
        dt = datetime.strptime(value, "%m/%d/%Y")
    elif fmt == 'unix':
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        return dt
    else:
        raise ValueError(f"Unknown format: {fmt}")
    
    return dt.replace(tzinfo=timezone.utc)

def format_date(dt: datetime, fmt: str) -> str:
    if fmt == 'iso':
        return dt.strftime("%Y-%m-%d")
    elif fmt == 'eu':
        return dt.strftime("%d-%m-%Y")
    elif fmt == 'us':
        return dt.strftime("%m/%d/%Y")
    elif fmt == 'unix':
        return str(int(dt.timestamp()))
    else:
        raise ValueError(f"Unknown format: {fmt}")

def detect_format(value: str) -> str:
    try:
        parse_date(value, 'iso')
        return 'iso'
    except ValueError:
        pass

    try:
        parse_date(value, 'eu')
        return 'eu'
    except ValueError:
        pass

    try:
        parse_date(value, 'us')
        return 'us'
    except ValueError:
        pass

    try:
        parse_date(value, 'unix')
        return 'unix'
    except ValueError:
        pass

    raise ValueError("Unrecognized date format")
