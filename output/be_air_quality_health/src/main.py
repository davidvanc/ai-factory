import argparse
from src.data_fetcher import fetch_pm_data, DataFetchError
from src.health_score import calculate_health_score
from src.report import display_report


class CityNotFoundError(Exception):
    pass


def generate_report(city: str) -> dict:
    try:
        data = fetch_pm_data(city)
    except DataFetchError as e:
        raise CityNotFoundError(f"No data available for city: {city}") from e
    pm25 = data["pm25"]
    pm10 = data["pm10"]
    health = calculate_health_score(pm25, pm10)
    report = {
        "city": city,
        "pm25": pm25,
        "pm10": pm10,
        "score": health["score"],
        "risk_level": health["risk_level"],
        "pm25_pct": health["pm25_pct"],
        "pm10_pct": health["pm10_pct"],
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Belgian Air Quality Health Risk Tool")
    parser.add_argument("city", help="City name (e.g., Brussels, Antwerp)")
    args = parser.parse_args()
    try:
        report = generate_report(args.city)
        display_report(report)
    except CityNotFoundError as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
