WHO_ANNUAL_PM2_5 = 5
WHO_24H_PM2_5 = 15
WHO_ANNUAL_PM10 = 15
WHO_24H_PM10 = 45


def get_exceedance_factor(value: float, standard: float) -> float:
    return value / standard
