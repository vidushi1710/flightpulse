
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
BASE_URL = "https://api.aviationstack.com/v1/flights"


def fetch_live_flights(departure_airport="JFK", limit=10):
    if not API_KEY:
        raise RuntimeError("Aviationstack API key not found in .env")

    params = {
        "access_key": API_KEY,
        "dep_iata": departure_airport.upper(),
        "limit": min(max(limit, 1), 100),
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    result = response.json()

    if result.get("error"):
        raise RuntimeError("Aviationstack returned an API error.")

    return result.get("data", [])
