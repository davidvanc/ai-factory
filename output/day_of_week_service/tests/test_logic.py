from src.logic import calculate_day_of_week_zeller

def test_zeller_friday():
    assert calculate_day_of_week_zeller(2024, 3, 15) == "Friday"

def test_zeller_monday():
    assert calculate_day_of_week_zeller(2000, 1, 3) == "Monday"

def test_zeller_leap_year_saturday():
    assert calculate_day_of_week_zeller(2020, 2, 29) == "Saturday"

def test_zeller_jan_feb_adjustment():
    # 2023-01-01 was Sunday
    assert calculate_day_of_week_zeller(2023, 1, 1) == "Sunday"
    # 2023-02-28 was Tuesday
    assert calculate_day_of_week_zeller(2023, 2, 28) == "Tuesday"
