from datetime import datetime, timezone
from src.time_service import get_current_time

class TestTimeService:
    def test_get_current_time_returns_datetime_object(self):
        result = get_current_time()
        assert isinstance(result, datetime)

    def test_get_current_time_is_timezone_aware(self):
        result = get_current_time()
        # timezone-aware objects have tzinfo not None
        assert result.tzinfo is not None
        # For UTC, tzinfo should be timezone.utc or equivalent
        assert result.tzinfo == timezone.utc or result.tzinfo.utcoffset(result) == timezone.utc.utcoffset(result)
