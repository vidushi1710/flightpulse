from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "flights.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "flights_cleaned.csv"


def main():
    print("Loading original flight dataset...")

    required_columns = [
        "YEAR",
        "MONTH",
        "DAY",
        "DAY_OF_WEEK",
        "AIRLINE",
        "ORIGIN_AIRPORT",
        "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE",
        "SCHEDULED_ARRIVAL",
        "DEPARTURE_DELAY",
        "DISTANCE",
        "DIVERTED",
        "CANCELLED",
    ]

    flights = pd.read_csv(
        RAW_FILE,
        usecols=required_columns,
        low_memory=False,
        dtype={
            "AIRLINE": "category",
            "ORIGIN_AIRPORT": "category",
            "DESTINATION_AIRPORT": "category",
        },
    )

    print("Original shape:", flights.shape)

    flights = flights[
        (flights["CANCELLED"] == 0) &
        (flights["DIVERTED"] == 0)
    ].copy()

    numeric_columns = [
        "YEAR",
        "MONTH",
        "DAY",
        "DAY_OF_WEEK",
        "SCHEDULED_DEPARTURE",
        "SCHEDULED_ARRIVAL",
        "DEPARTURE_DELAY",
        "DISTANCE",
    ]

    for col in numeric_columns:
        flights[col] = pd.to_numeric(
            flights[col], errors="coerce"
        )

    flights.dropna(
        subset=numeric_columns,
        inplace=True
    )

    flights.drop_duplicates(inplace=True)

    flights["FLIGHT_DATE"] = pd.to_datetime(
        flights[["YEAR", "MONTH", "DAY"]].rename(
            columns={
                "YEAR": "year",
                "MONTH": "month",
                "DAY": "day",
            }
        ),
        errors="coerce",
    )

    flights.dropna(subset=["FLIGHT_DATE"], inplace=True)

    flights["DEP_HOUR"] = (
        flights["SCHEDULED_DEPARTURE"] // 100
    ).astype(int)

    flights["ARR_HOUR"] = (
        flights["SCHEDULED_ARRIVAL"] // 100
    ).astype(int)

    flights["DEP_HOUR"] = flights["DEP_HOUR"].replace(24, 0)
    flights["ARR_HOUR"] = flights["ARR_HOUR"].replace(24, 0)

    # Target: departure delay of 15 minutes or more
    flights["IS_DELAYED"] = (
        flights["DEPARTURE_DELAY"] >= 15
    ).astype("int8")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    flights.to_csv(OUTPUT_FILE, index=False)

    print("\nCleaning completed successfully!")
    print("Cleaned shape:", flights.shape)
    print("Saved dataset:", OUTPUT_FILE)

    print("\nDelay label distribution:")
    print(flights["IS_DELAYED"].value_counts().sort_index())

    print(
        "\nDelayed-flight percentage:",
        round(flights["IS_DELAYED"].mean() * 100, 2),
        "%"
    )

    print("\nDeparture delay statistics:")
    print(flights["DEPARTURE_DELAY"].describe())

    print("\nDate range:")
    print(flights["FLIGHT_DATE"].min())
    print("to")
    print(flights["FLIGHT_DATE"].max())


if __name__ == "__main__":
    main()