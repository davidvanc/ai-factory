import os
from dotenv import load_dotenv

load_dotenv()

AQICN_TOKEN = os.getenv("AQICN_TOKEN", "")
IRCEL_BASE_URL = "https://irceline.be/api/v1"
OPENDATA_BRUSSELS_URL = "https://opendata.brussels.be/api/records/1.0/search/"
