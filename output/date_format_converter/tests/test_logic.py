import pytest
from datetime import datetime, timezone
from src.logic import parse_date, format_date, detect_format

def test_parse_date_iso():
    dt = parse_date("2023-12-25", "iso")
    assert dt.year == 2023
    assert dt.month == 12
    assert dt.day == 25
    assert dt.tzinfo == timezone.utc

def test_parse_date_invalid():
    with pytest.raises(ValueError):
        parse_date("31-02-2023", "eu")

def test_format_date_iso():
    dt = datetime(2023, 12, 25, tzinfo=timezone.utc)
    assert format_date(dt, "iso") == "2023-12-25"

def test_detect_format():
    assert detect_format("2023-12-25") == "iso"
    assert detect_format("25-12-2023") == "eu"
    assert detect_format("12/25/2023") == "us"
    assert detect_format("1703462400") == "unix"

def test_detect_format_invalid():
    with pytest.raises(ValueError):
        detect_format("invalid-date")
