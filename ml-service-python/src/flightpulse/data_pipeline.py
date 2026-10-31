
from pathlib import Path
import pandas as pd

# Locate the ml-service-python directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "flights.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "flights_cleaned.csv"

REQUIRED_COLUMNS = [
    "YEAR",
    "MONTH",
    "DAY",
    "DAY_OF_WEEK",
    "AIRLINE",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE",
    "SCHEDULED_ARRIVAL",
    "DISTANCE",
    "ARRIVAL_DELAY",
    "DIVERTED",
    "CANCELLED",
]


def build_clean_dataset():
    # 1. Check that the original dataset exists
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_FILE}"
        )

    print("Loading original flight dataset...")

    # 2. Load only the columns we need
    flights = pd.read_csv(
        RAW_FILE,
        usecols=REQUIRED_COLUMNS,
        dtype={
            "ORIGIN_AIRPORT": "string",
            "DESTINATION_AIRPORT": "string",
        },
        low_memory=False,
    )

    print("Original shape:", flights.shape)

    # 3. Remove cancelled and diverted flights
    flights = flights.loc[
        (flights["CANCELLED"] == 0)
        & (flights["DIVERTED"] == 0)
    ].copy()

    # 4. Remove rows without an arrival delay
    flights = flights.dropna(
        subset=["ARRIVAL_DELAY"]
    ).copy()

    # 5. Convert required numeric columns safely
    numeric_columns = [
        "YEAR",
        "MONTH",
        "DAY",
        "DAY_OF_WEEK",
        "SCHEDULED_DEPARTURE",
        "SCHEDULED_ARRIVAL",
        "DISTANCE",
        "ARRIVAL_DELAY",
    ]

    for column in numeric_columns:
        flights[column] = pd.to_numeric(
            flights[column],
            errors="coerce",
        )

    flights = flights.dropna(
        subset=numeric_columns
    ).copy()

    # 6. Remove exact duplicate rows
    flights = flights.drop_duplicates().copy()

    # 7. Create the flight date
    flights["FLIGHT_DATE"] = pd.to_datetime(
        {
            "year": flights["YEAR"].astype(int),
            "month": flights["MONTH"].astype(int),
            "day": flights["DAY"].astype(int),
        },
        errors="coerce",
    )

    flights = flights.dropna(
        subset=["FLIGHT_DATE"]
    ).copy()

    # 8. Extract scheduled departure hour
    departure_time = flights[
        "SCHEDULED_DEPARTURE"
    ].astype(int)

    flights["DEP_HOUR"] = departure_time // 100

    # Handle midnight represented as 2400
    flights.loc[
        flights["DEP_HOUR"] == 24,
        "DEP_HOUR",
    ] = 0

    # 9. Create the classification target:
    # 1 = arrival delay of 15 minutes or more
    # 0 = arrival delay below 15 minutes
    flights["IS_DELAYED"] = (
        flights["ARRIVAL_DELAY"] >= 15
    ).astype("int8")

    # 10. Save the cleaned dataset
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    flights.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # 11. Display a summary
    print("\nCleaning completed successfully!")
    print("Cleaned shape:", flights.shape)
    print("Saved dataset:", OUTPUT_FILE)

    print("\nDelay label distribution:")
    print(
        flights["IS_DELAYED"].value_counts().sort_index()
    )

    print(
        "\nDelayed-flight percentage:",
        round(flights["IS_DELAYED"].mean() * 100, 2),
        "%",
    )

    print("\nDate range:")
    print(flights["FLIGHT_DATE"].min())
    print("to")
    print(flights["FLIGHT_DATE"].max())

    return flights


if __name__ == "__main__":
    build_clean_dataset()
