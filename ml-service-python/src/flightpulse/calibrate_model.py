import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

DATA = Path("data/processed/flights_cleaned.csv")
MODEL = Path("models/flight_delay_model.pkl")
CALIBRATOR = Path("models/probability_calibrator.pkl")

columns = [
    "FLIGHT_DATE", "MONTH", "DAY_OF_WEEK", "AIRLINE",
    "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE", "SCHEDULED_ARRIVAL",
    "DISTANCE", "IS_DELAYED"
]

print("Loading data...")
df = pd.read_csv(DATA, usecols=columns, low_memory=False)
df["FLIGHT_DATE"] = pd.to_datetime(df["FLIGHT_DATE"])
df["DEP_HOUR"] = (df["SCHEDULED_DEPARTURE"] // 100).astype(int).replace(24, 0)
df["ARR_HOUR"] = (df["SCHEDULED_ARRIVAL"] // 100).astype(int).replace(24, 0)

FEATURES = [
    "MONTH", "DAY_OF_WEEK", "DEP_HOUR", "ARR_HOUR",
    "DISTANCE", "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"
]

df = df.dropna(subset=FEATURES + ["IS_DELAYED"])

validation = df[
    (df["FLIGHT_DATE"] >= "2015-10-01") &
    (df["FLIGHT_DATE"] < "2015-12-01")
].sample(n=100000, random_state=42)

test = df[df["FLIGHT_DATE"] >= "2015-12-01"].sample(
    n=100000, random_state=42
)

model = joblib.load(MODEL)

print("Generating probabilities...")
val_probs = model.predict_proba(validation[FEATURES])[:, 1]
test_probs = model.predict_proba(test[FEATURES])[:, 1]

calibrator = IsotonicRegression(out_of_bounds="clip")
calibrator.fit(val_probs, validation["IS_DELAYED"].astype(int))

calibrated = calibrator.predict(test_probs)

joblib.dump(calibrator, CALIBRATOR)

y = test["IS_DELAYED"].astype(int)

print("\n===== ISOTONIC CALIBRATION RESULTS =====")
print("Actual delay rate:", round(y.mean() * 100, 2), "%")
print("Original mean probability:", round(test_probs.mean() * 100, 2), "%")
print("Calibrated mean probability:", round(calibrated.mean() * 100, 2), "%")
print("Original Brier:", round(brier_score_loss(y, test_probs), 4))
print("Calibrated Brier:", round(brier_score_loss(y, calibrated), 4))
print("Original Log Loss:", round(log_loss(y, test_probs), 4))
print("Calibrated Log Loss:", round(log_loss(y, calibrated), 4))
print("ROC-AUC:", round(roc_auc_score(y, calibrated), 4))

test = test.copy()
test["PROBABILITY"] = calibrated
test["ACTUAL"] = y.values
test["BUCKET"] = pd.cut(
    test["PROBABILITY"],
    bins=[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1],
    include_lowest=True
)

print("\n===== CALIBRATION BUCKETS =====")
print(
    test.groupby("BUCKET", observed=False)
    .agg(
        Flights=("ACTUAL", "count"),
        Predicted=("PROBABILITY", "mean"),
        Actual=("ACTUAL", "mean")
    ).to_string()
)

print("\nCalibrator saved:", CALIBRATOR)
