from datetime import datetime, timezone

def get_current_time() -> datetime:
    """Returns the current UTC time as a timezone-aware datetime object."""
    return datetime.now(timezone.utc)
