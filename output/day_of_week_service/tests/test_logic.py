from src.logic import calculate_day_of_week

def test_calculate_day_of_week_standard():
    assert calculate_day_of_week("2025-01-15") == "Wednesday"

def test_calculate_day_of_week_saturday():
    assert calculate_day_of_week("2000-01-01") == "Saturday"

def test_calculate_day_of_week_leap_year():
    assert calculate_day_of_week("2024-02-29") == "Thursday"

def test_calculate_day_of_week_jan_feb():
    assert calculate_day_of_week("2023-02-01") == "Wednesday"
