from datetime import datetime, timezone


def generate_report(location: str, pm2_5: float, pm10: float, score: int, classification: str) -> dict:
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'location': location,
        'pm2_5': pm2_5,
        'pm10': pm10,
        'risk_score': score,
        'classification': classification
    }
