import argparse
import sys
import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from tabulate import tabulate

from src.data_fetcher import fetch_aqicn, fetch_openaq
from src.health_score import get_health_score
from src.report import generate_report

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEFAULT_CITIES = ["Brussel", "Antwerpen", "Gent", "Luik"]


def get_air_quality(city: str):
    try:
        data = fetch_aqicn(city)
        if data['pm2_5'] is None and data['pm10'] is None:
            raise ValueError("aqicn returned no data")
        return data
    except Exception as e:
        logging.warning(f"Primary source (aqicn) failed for {city}: {e}. Falling back to OpenAQ.")
        try:
            data = fetch_openaq(city)
            return data
        except Exception as e2:
            logging.error(f"Fallback source (OpenAQ) also failed for {city}: {e2}")
            raise


def process_cities(cities: list):
    reports = []
    for city in cities:
        try:
            pm = get_air_quality(city)
            pm2_5 = pm['pm2_5'] if pm['pm2_5'] is not None else 0
            pm10 = pm['pm10'] if pm['pm10'] is not None else 0
            health = get_health_score(pm2_5, pm10)
            report = generate_report(city, pm2_5, pm10, health['score'], health['classification'])
            reports.append(report)
            logging.info(f"{city}: PM2.5={pm2_5}, PM10={pm10}, Score={health['score']}, Classification={health['classification']}")
        except Exception as e:
            logging.error(f"Could not retrieve data for {city}: {e}")
    return reports


class AirQualityHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        elif parsed.path.startswith('/airquality'):
            city = params.get('city', [None])[0]
            if not city:
                self.send_error(400, "Missing city parameter")
                return
            try:
                pm = get_air_quality(city)
                pm2_5 = pm['pm2_5'] if pm['pm2_5'] is not None else 0
                pm10 = pm['pm10'] if pm['pm10'] is not None else 0
                health = get_health_score(pm2_5, pm10)
                report = generate_report(city, pm2_5, pm10, health['score'], health['classification'])
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(report).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not Found")


def start_web_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), AirQualityHandler)
    print(f"Starting web server on port {port}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Belgium Air Quality Monitor")
    parser.add_argument('--cities', nargs='+', default=DEFAULT_CITIES, help="List of cities to monitor")
    parser.add_argument('--json', action='store_true', help="Output as JSON")
    parser.add_argument('--web', action='store_true', help="Start web server on port 8080")
    parser.add_argument('--port', type=int, default=8080, help="Port for web server (default 8080)")
    args = parser.parse_args()

    if args.web:
        start_web_server(args.port)
    else:
        reports = process_cities(args.cities)
        if args.json:
            print(json.dumps(reports, indent=2))
        else:
            table = []
            for r in reports:
                table.append([r['location'], r['pm2_5'], r['pm10'], r['risk_score'], r['classification']])
            print(tabulate(table, headers=['City', 'PM2.5', 'PM10', 'Score', 'Classification']))


if __name__ == '__main__':
    main()
