import os
import requests


def fetch_aqicn(city: str):
    token = os.getenv('AQICN_TOKEN')
    if not token:
        raise ValueError("AQICN_TOKEN environment variable not set")
    url = f"https://api.waqi.info/feed/{city}/?token={token}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get('status') != 'ok':
        raise Exception(f"aqicn API error: {data.get('data', 'unknown')}")
    iaqi = data['data'].get('iaqi', {})
    pm2_5 = None
    pm10 = None
    if 'pm25' in iaqi:
        pm2_5 = float(iaqi['pm25']['v'])
    if 'pm10' in iaqi:
        pm10 = float(iaqi['pm10']['v'])
    return {'pm2_5': pm2_5, 'pm10': pm10}


def fetch_openaq(city: str):
    api_key = os.getenv('OPENAQ_API_KEY')
    headers = {}
    if api_key:
        headers['X-API-Key'] = api_key
    url = "https://api.openaq.org/v2/measurements"
    params = {
        'city': city,
        'parameter': ['pm25', 'pm10'],
        'limit': 100,
        'country': 'BE',
        'order_by': 'desc',
        'sort': 'datetime',
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get('results', [])
    pm2_5 = None
    pm10 = None
    for measurement in results:
        if measurement['parameter'] == 'pm25' and pm2_5 is None:
            pm2_5 = measurement['value']
        elif measurement['parameter'] == 'pm10' and pm10 is None:
            pm10 = measurement['value']
        if pm2_5 is not None and pm10 is not None:
            break
    return {'pm2_5': pm2_5, 'pm10': pm10}
