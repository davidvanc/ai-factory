# WHO air quality guidelines (µg/m³)
WHO_24H_PM25 = 15
WHO_24H_PM10 = 45
WHO_ANNUAL_PM25 = 5
WHO_ANNUAL_PM10 = 15


def get_24h_thresholds():
    return {"pm25": WHO_24H_PM25, "pm10": WHO_24H_PM10}


def get_annual_thresholds():
    return {"pm25": WHO_ANNUAL_PM25, "pm10": WHO_ANNUAL_PM10}
