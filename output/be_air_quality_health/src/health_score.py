from src.who_standards import WHO_24H_PM25, WHO_24H_PM10


def calculate_health_score(pm25: float, pm10: float) -> dict:
    # Calculate percentage of 24h guideline
    pm25_pct = (pm25 / WHO_24H_PM25) * 100
    pm10_pct = (pm10 / WHO_24H_PM10) * 100
    max_pct = max(pm25_pct, pm10_pct)

    # Determine risk level
    if max_pct <= 100:
        risk_level = "low"
    elif max_pct <= 200:
        risk_level = "moderate"
    elif max_pct <= 300:
        risk_level = "high"
    else:
        risk_level = "very high"

    # Compute score 0-100 (capped)
    # Map max_pct to 0-100: linear up to 300% -> 100, above 300% -> 100
    score = min(100, (max_pct / 300) * 100)
    score = round(score, 1)

    return {
        "score": score,
        "risk_level": risk_level,
        "pm25_pct": round(pm25_pct, 1),
        "pm10_pct": round(pm10_pct, 1),
    }
