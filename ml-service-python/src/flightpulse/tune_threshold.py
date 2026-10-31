from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    accuracy_score, roc_auc_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "flights_cleaned.csv"
MODEL_FILE = PROJECT_ROOT / "models" / "flight_delay_model.pkl"
RANDOM_STATE = 42


def load_validation_and_test():
    columns = [
        "FLIGHT_DATE", "MONTH", "DAY_OF_WEEK", "AIRLINE",
        "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "SCHEDULED_ARRIVAL",
        "DISTANCE", "IS_DELAYED",
    ]
    flights = pd.read_csv(
        DATA_FILE,
        usecols=columns,
        dtype={
            "AIRLINE": "string",
            "ORIGIN_AIRPORT": "string",
            "DESTINATION_AIRPORT": "string",
        },
    )
    flights["FLIGHT_DATE"] = pd.to_datetime(flights["FLIGHT_DATE"])
    validation = flights[
        (flights["FLIGHT_DATE"] >= "2015-10-01")
        & (flights["FLIGHT_DATE"] < "2015-12-01")
    ].sample(n=100_000, random_state=RANDOM_STATE)
    test = flights[
        flights["FLIGHT_DATE"] >= "2015-12-01"
    ].sample(n=100_000, random_state=RANDOM_STATE)
    return validation, test


def prepare_features(data):
    data = data.copy()
    data["DEP_HOUR"] = data["SCHEDULED_DEPARTURE"] // 100
    data["ARR_HOUR"] = data["SCHEDULED_ARRIVAL"] // 100
    data.loc[data["DEP_HOUR"] == 24, "DEP_HOUR"] = 0
    data.loc[data["ARR_HOUR"] == 24, "ARR_HOUR"] = 0
    features = [
        "MONTH", "DAY_OF_WEEK", "DEP_HOUR", "ARR_HOUR",
        "DISTANCE", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
    ]
    return data[features], data["IS_DELAYED"].astype(int)


def main():
    print("Loading trained model...")
    model = joblib.load(MODEL_FILE)
    print("Loading validation and test data...")
    validation, test = load_validation_and_test()
    X_val, y_val = prepare_features(validation)
    X_test, y_test = prepare_features(test)

    print("\nGenerating validation probabilities...")
    val_probabilities = model.predict_proba(X_val)[:, 1]
    thresholds = [
        0.10, 0.15, 0.20, 0.25, 0.30, 0.35,
        0.40, 0.45, 0.50, 0.55, 0.60,
    ]
    best_threshold = 0.50
    best_f1 = -1

    print("\nVALIDATION THRESHOLD COMPARISON")
    print("-" * 55)
    for threshold in thresholds:
        predictions = (val_probabilities >= threshold).astype(int)
        precision = precision_score(y_val, predictions, zero_division=0)
        recall = recall_score(y_val, predictions, zero_division=0)
        f1 = f1_score(y_val, predictions, zero_division=0)
        print(
            f"Threshold: {threshold:.2f} | Precision: {precision:.4f} | "
            f"Recall: {recall:.4f} | F1: {f1:.4f}"
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print("\nBest validation threshold:", best_threshold)
    print("Best validation F1:", round(best_f1, 4))

    print("\nEvaluating selected threshold on untouched test data...")
    test_probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (test_probabilities >= best_threshold).astype(int)

    print("\nFINAL TEST RESULTS — Threshold:", best_threshold)
    print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
    print("Precision:", round(precision_score(y_test, predictions, zero_division=0), 4))
    print("Recall:", round(recall_score(y_test, predictions, zero_division=0), 4))
    print("F1:", round(f1_score(y_test, predictions, zero_division=0), 4))
    print("ROC-AUC:", round(roc_auc_score(y_test, test_probabilities), 4))

    threshold_file = PROJECT_ROOT / "models" / "threshold.json"
    threshold_file.parent.mkdir(parents=True, exist_ok=True)
    with open(threshold_file, "w", encoding="utf-8") as file:
        json.dump({"classification_threshold": best_threshold}, file, indent=4)
    print("\nThreshold saved to:", threshold_file)


if __name__ == "__main__":
    main()
