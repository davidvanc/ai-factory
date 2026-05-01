def get_health_score(pm2_5: float, pm10: float = None):
    # Classificatie op basis van PM2.5
    if pm2_5 < 5:
        classification = "Goed"
    elif pm2_5 < 10:
        classification = "Matig"
    elif pm2_5 < 15:
        classification = "Ongezond voor gevoelige groepen"
    elif pm2_5 < 25:
        classification = "Ongezond"
    else:
        classification = "Zeer ongezond"

    # Score: 0-100, gebaseerd op PM2.5 (tot max 100 als > 25)
    if pm2_5 <= 0:
        score = 0
    else:
        score = min(100, int(round((pm2_5 / 25) * 100)))
    return {'score': score, 'classification': classification}
