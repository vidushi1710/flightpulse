from pathlib import Path
import pandas as pd
import joblib

from sklearn.metrics import (
    roc_auc_score,
    brier_score_loss,
    log_loss,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "flights_cleaned.csv"
MODEL = ROOT / "models" / "flight_delay_model.pkl"

model = joblib.load(MODEL)

columns = [
    "FLIGHT_DATE",
    "MONTH",
    "DAY_OF_WEEK",
    "AIRLINE",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE",
    "SCHEDULED_ARRIVAL",
    "DISTANCE",
    "IS_DELAYED",
]

print("Loading dataset...")
flights = pd.read_csv(DATA, usecols=columns)
flights["FLIGHT_DATE"] = pd.to_datetime(flights["FLIGHT_DATE"])

test = flights[flights["FLIGHT_DATE"] >= "2015-12-01"].copy()
test = test.sample(n=min(100_000, len(test)), random_state=42)

test["DEP_HOUR"] = test["SCHEDULED_DEPARTURE"] // 100
test["ARR_HOUR"] = test["SCHEDULED_ARRIVAL"] // 100

test.loc[test["DEP_HOUR"] == 24, "DEP_HOUR"] = 0
test.loc[test["ARR_HOUR"] == 24, "ARR_HOUR"] = 0

features = [
    "MONTH",
    "DAY_OF_WEEK",
    "DEP_HOUR",
    "ARR_HOUR",
    "DISTANCE",
    "AIRLINE",
    "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT",
]

X = test[features]
y = test["IS_DELAYED"].astype(int)

probabilities = model.predict_proba(X)[:, 1]

print("\n===== MODEL AUDIT =====")
print("Test size:", len(test))
print("Actual delay rate:", round(y.mean() * 100, 2), "%")
print("Mean predicted probability:", round(probabilities.mean() * 100, 2), "%")
print("Median probability:", round(pd.Series(probabilities).median() * 100, 2), "%")
print("Minimum probability:", round(probabilities.min() * 100, 2), "%")
print("Maximum probability:", round(probabilities.max() * 100, 2), "%")
print("ROC-AUC:", round(roc_auc_score(y, probabilities), 4))
print("Brier score:", round(brier_score_loss(y, probabilities), 4))
print("Log loss:", round(log_loss(y, probabilities), 4))

test["PREDICTED_PROBABILITY"] = probabilities
test["ACTUAL_DELAY"] = y

test["PROBABILITY_BUCKET"] = pd.cut(
    test["PREDICTED_PROBABILITY"],
    bins=[0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0],
    include_lowest=True,
)

print("\n===== CALIBRATION BY PROBABILITY =====")
print(
    test.groupby("PROBABILITY_BUCKET", observed=False)
    .agg(
        Flights=("ACTUAL_DELAY", "count"),
        MeanPredicted=("PREDICTED_PROBABILITY", "mean"),
        ActualDelayRate=("ACTUAL_DELAY", "mean"),
    )
    .to_string()
)

print("\nAudit completed.")
