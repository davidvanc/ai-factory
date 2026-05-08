def calculate_day_of_week_zeller(year: int, month: int, day: int) -> str:
    """
    Calculates the day of the week for a given date using Zeller's congruence.
    """
    if month < 3:
        month += 12
        year -= 1

    q = day
    m = month
    K = year % 100
    J = year // 100

    h = (q + (13 * (m + 1)) // 5 + K + (K // 4) + (J // 4) - 2 * J) % 7

    days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return days[h]
