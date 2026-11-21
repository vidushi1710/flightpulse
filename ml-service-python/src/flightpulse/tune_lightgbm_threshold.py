import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

DATA = "data/processed/flights_cleaned.csv"
MODEL_PATH = "models/flightpulse_lightgbm.pkl"

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
CATEGORICAL = ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]

df = df.dropna(subset=FEATURES + ["IS_DELAYED"])

for col in CATEGORICAL:
    df[col] = df[col].astype("category")

val = df[
    (df["FLIGHT_DATE"] >= "2015-10-01") &
    (df["FLIGHT_DATE"] < "2015-12-01")
].sample(n=100000, random_state=42)

test = df[df["FLIGHT_DATE"] >= "2015-12-01"].sample(
    n=100000, random_state=42
)

model = joblib.load(MODEL_PATH)

print("Predicting validation...")
val_probs = model.predict_proba(val[FEATURES])[:, 1]
y_val = val["IS_DELAYED"].astype(int)

thresholds = np.arange(0.05, 0.51, 0.01)
results = []

for threshold in thresholds:
    pred = (val_probs >= threshold).astype(int)
    results.append({
        "threshold": threshold,
        "precision": precision_score(y_val, pred, zero_division=0),
        "recall": recall_score(y_val, pred, zero_division=0),
        "f1": f1_score(y_val, pred, zero_division=0),
        "accuracy": accuracy_score(y_val, pred)
    })

results = pd.DataFrame(results)
best = results.loc[results["f1"].idxmax()]

print("\n===== VALIDATION THRESHOLD SEARCH =====")
print(results.sort_values("f1", ascending=False).head(10).to_string(index=False))

threshold = float(best["threshold"])
print("\nSelected threshold:", round(threshold, 3))

print("\nEvaluating on December test data...")
test_probs = model.predict_proba(test[FEATURES])[:, 1]
y_test = test["IS_DELAYED"].astype(int)
pred = (test_probs >= threshold).astype(int)

print("\n===== TEST RESULTS AT SELECTED THRESHOLD =====")
print("Threshold:", round(threshold, 3))
print("Accuracy:", round(accuracy_score(y_test, pred), 4))
print("Precision:", round(precision_score(y_test, pred, zero_division=0), 4))
print("Recall:", round(recall_score(y_test, pred, zero_division=0), 4))
print("F1:", round(f1_score(y_test, pred, zero_division=0), 4))
print("Predicted delayed:", int(pred.sum()))
print("Actual delayed:", int(y_test.sum()))

print("\nThreshold tuning complete.")
