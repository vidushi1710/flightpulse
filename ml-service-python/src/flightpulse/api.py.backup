import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import joblib
import pandas as pd
import requests

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.flightpulse.aviationstack import fetch_live_flights


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = PROJECT_ROOT / "models" / "flightpulse_lightgbm.pkl"
ROUTE_FILE = PROJECT_ROOT / "data" / "processed" / "route_distances.json"

for file_path in [MODEL_FILE, ROUTE_FILE]:
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")

model = joblib.load(MODEL_FILE)

with open(ROUTE_FILE, "r") as file:
    ROUTE_DISTANCES = json.load(file)

CLASSIFICATION_THRESHOLD = 0.14

FEATURES = [
    "MONTH", "DAY_OF_WEEK", "DEP_HOUR", "ARR_HOUR",
    "DISTANCE", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"
]

CAT_COLS = ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]

# Recover the categorical levels stored with the trained LightGBM model.
CATEGORY_LEVELS = getattr(model.booster_, "pandas_categorical", None)

if CATEGORY_LEVELS is None:
    raise RuntimeError("LightGBM categorical metadata is missing.")

AIRLINE_CODES = set(str(x) for x in CATEGORY_LEVELS[0])
AIRPORT_CODES = set(str(x) for x in CATEGORY_LEVELS[1])


app = FastAPI(
    title="FlightPulse API",
    description="Experimental flight delay risk prediction service using historical ML and live flight data.",
    version="2.0.0",
)


class FlightInput(BaseModel):
    MONTH: int = Field(ge=1, le=12)
    DAY_OF_WEEK: int = Field(ge=1, le=7)
    DEP_HOUR: int = Field(ge=0, le=23)
    ARR_HOUR: int = Field(ge=0, le=23)
    DISTANCE: float = Field(gt=0)
    AIRLINE: str = Field(min_length=1)
    ORIGIN_AIRPORT: str = Field(min_length=1)
    DESTINATION_AIRPORT: str = Field(min_length=1)


def prepare_features(features):
    data = pd.DataFrame([features], columns=FEATURES)

    for i, col in enumerate(CAT_COLS):
        data[col] = pd.Categorical(
            data[col].astype(str),
            categories=CATEGORY_LEVELS[i]
        )

    return data


def predict_features(features):
    data = prepare_features(features)

    probability = float(model.predict_proba(data)[0][1])
    prediction = int(probability >= CLASSIFICATION_THRESHOLD)

    return {
        "delay_probability": round(probability, 4),
        "delay_percentage": round(probability * 100, 2),
        "prediction": prediction,
        "risk_level": "High" if prediction else "Low",
        "classification_threshold": CLASSIFICATION_THRESHOLD,
        "model": "LightGBM",
        "model_period": "2015 historical training data",
        "experimental_estimate": True,
    }


def local_scheduled_time(timestamp, timezone):
    if not timestamp or not timezone:
        raise ValueError("Scheduled timestamp or airport timezone is missing.")

    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        raise ValueError("Scheduled timestamp has no timezone information.")

    return parsed.astimezone(ZoneInfo(timezone))


def deduplicate_live_flights(flights):
    unique_flights = []
    seen = set()

    for flight in flights:
        flight_info = flight.get("flight") or {}
        departure = flight.get("departure") or {}
        arrival = flight.get("arrival") or {}
        codeshared = flight_info.get("codeshared") or {}

        operating_flight = (
            codeshared.get("flight_iata")
            or flight_info.get("iata")
            or flight_info.get("icao")
            or flight_info.get("number")
        )

        origin = (departure.get("iata") or "").upper()
        destination = (arrival.get("iata") or "").upper()
        scheduled = departure.get("scheduled") or ""

        key = (
            str(operating_flight).upper(),
            origin,
            destination,
            scheduled,
        )

        if key in seen:
            continue

        seen.add(key)
        unique_flights.append(flight)

    return unique_flights


def normalize_live_flight(flight):
    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}
    airline = flight.get("airline") or {}
    flight_info = flight.get("flight") or {}
    codeshared = flight_info.get("codeshared") or {}

    airline_code = (
        codeshared.get("airline_iata")
        or airline.get("iata")
        or ""
    ).upper()

    origin = (departure.get("iata") or "").upper()
    destination = (arrival.get("iata") or "").upper()

    flight_number = (
        codeshared.get("flight_iata")
        or flight_info.get("iata")
        or flight_info.get("number")
    )

    missing = []

    if airline_code not in AIRLINE_CODES:
        missing.append(f"Unsupported airline: {airline_code or 'missing'}")

    if origin not in AIRPORT_CODES:
        missing.append(f"Unsupported origin airport: {origin or 'missing'}")

    if destination not in AIRPORT_CODES:
        missing.append(f"Unsupported destination airport: {destination or 'missing'}")

    if missing:
        return {
            "flight_number": flight_number,
            "airline": airline_code,
            "origin": origin,
            "destination": destination,
            "status": "not_supported",
            "reasons": missing,
        }

    route_key = f"{origin}|{destination}"
    distance = ROUTE_DISTANCES.get(route_key)

    if distance is None:
        return {
            "flight_number": flight_number,
            "airline": airline_code,
            "origin": origin,
            "destination": destination,
            "status": "distance_unavailable",
            "reasons": ["No verified historical route distance found."],
        }

    try:
        departure_time = local_scheduled_time(
            departure.get("scheduled"),
            departure.get("timezone"),
        )

        arrival_time = local_scheduled_time(
            arrival.get("scheduled"),
            arrival.get("timezone"),
        )

    except (ValueError, TypeError, KeyError) as error:
        return {
            "flight_number": flight_number,
            "status": "incomplete_data",
            "reasons": [str(error)],
        }

    features = {
        "MONTH": departure_time.month,
        "DAY_OF_WEEK": departure_time.isoweekday(),
        "DEP_HOUR": departure_time.hour,
        "ARR_HOUR": arrival_time.hour,
        "DISTANCE": float(distance),
        "AIRLINE": airline_code,
        "ORIGIN_AIRPORT": origin,
        "DESTINATION_AIRPORT": destination,
    }

    prediction = predict_features(features)

    return {
        "flight_number": flight_number,
        "airline": airline_code,
        "origin": origin,
        "destination": destination,
        "departure_local": departure_time.isoformat(),
        "arrival_local": arrival_time.isoformat(),
        "distance_miles": distance,
        "status": "predicted",
        "prediction": prediction,
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to FlightPulse API",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_name": "LightGBM",
        "classification_threshold": CLASSIFICATION_THRESHOLD,
        "supported_airlines": len(AIRLINE_CODES),
        "supported_airports": len(AIRPORT_CODES),
        "historical_routes": len(ROUTE_DISTANCES),
    }


@app.post("/predict")
def predict_flight(flight: FlightInput):
    if flight.AIRLINE not in AIRLINE_CODES:
        raise HTTPException(status_code=422, detail="Unsupported airline code.")

    if flight.ORIGIN_AIRPORT not in AIRPORT_CODES:
        raise HTTPException(status_code=422, detail="Unsupported origin airport.")

    if flight.DESTINATION_AIRPORT not in AIRPORT_CODES:
        raise HTTPException(status_code=422, detail="Unsupported destination airport.")

    return predict_features(flight.model_dump())


@app.get("/live-flights")
def live_flights(
    departure_airport: str = Query(default="JFK", min_length=3, max_length=3),
    limit: int = Query(default=10, ge=1, le=100),
):
    try:
        flights = fetch_live_flights(departure_airport, limit)
        unique_flights = deduplicate_live_flights(flights)

        results = [
            normalize_live_flight(flight)
            for flight in unique_flights
        ]

        predicted_count = sum(
            1 for flight in results if flight["status"] == "predicted"
        )

        return {
            "source": "Aviationstack",
            "model": "LightGBM",
            "departure_airport": departure_airport.upper(),
            "total_flights_received": len(flights),
            "unique_flights": len(unique_flights),
            "duplicates_removed": len(flights) - len(unique_flights),
            "predicted_flights": predicted_count,
            "flights": results,
            "note": (
                "Predictions use a model trained on 2015 historical data. "
                "These are experimental estimates, not guaranteed live forecasts."
            ),
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve live flight data."
        )

    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))
