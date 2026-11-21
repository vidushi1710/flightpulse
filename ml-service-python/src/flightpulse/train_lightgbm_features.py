import pandas as pd
import numpy as np
import joblib
import os

from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, brier_score_loss,
    log_loss
)

print("Loading cleaned data...")
df = pd.read_csv("data/processed/flights_cleaned.csv")

df["FLIGHT_DATE"] = pd.to_datetime(df["FLIGHT_DATE"])

FEATURES = [
    "MONTH", "DAY_OF_WEEK", "DEP_HOUR", "ARR_HOUR",
    "DISTANCE", "AIRLINE", "ORIGIN_AIRPORT",
    "DESTINATION_AIRPORT"
]

CAT_COLS = ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]

df[CAT_COLS] = df[CAT_COLS].astype(str)

train_period = df[df["FLIGHT_DATE"] < "2015-10-01"].copy()
val_period = df[
    (df["FLIGHT_DATE"] >= "2015-10-01") &
    (df["FLIGHT_DATE"] < "2015-12-01")
].copy()
test_period = df[df["FLIGHT_DATE"] >= "2015-12-01"].copy()

# Separate aggregate reference data from model training data
# to prevent target leakage.
aggregate_reference = train_period[
    train_period["FLIGHT_DATE"] < "2015-08-01"
].copy()

model_training_period = train_period[
    train_period["FLIGHT_DATE"] >= "2015-08-01"
].copy()

print("Aggregate reference rows:", len(aggregate_reference))
print("Model training rows:", len(model_training_period))
print("Validation rows:", len(val_period))
print("Test rows:", len(test_period))

TARGET = "IS_DELAYED"

global_rate = aggregate_reference[TARGET].mean()
print("Reference delay rate:", round(global_rate, 4))

def build_aggregates(reference):
    mappings = {}

    groupings = {
        "AIRLINE": ["AIRLINE"],
        "ORIGIN": ["ORIGIN_AIRPORT"],
        "DESTINATION": ["DESTINATION_AIRPORT"],
        "ROUTE": ["ORIGIN_AIRPORT", "DESTINATION_AIRPORT"],
        "AIRLINE_ROUTE": ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"],
        "AIRLINE_HOUR": ["AIRLINE", "DEP_HOUR"],
        "ORIGIN_HOUR": ["ORIGIN_AIRPORT", "DEP_HOUR"],
    }

    for name, columns in groupings.items():
        stats = reference.groupby(columns, observed=True)[TARGET].agg(
            ["mean", "count"]
        )

        # Smooth small groups toward the overall reference rate.
        smoothed = (
            stats["mean"] * stats["count"] +
            global_rate * 100
        ) / (stats["count"] + 100)

        mappings[name] = smoothed
        mappings[name + "_COUNT"] = stats["count"]

    return mappings

print("Building historical aggregate features...")
mappings = build_aggregates(aggregate_reference)

def add_features(data):
    data = data.copy()

    data["AIRLINE_DELAY_RATE"] = data["AIRLINE"].map(mappings["AIRLINE"])
    data["ORIGIN_DELAY_RATE"] = data["ORIGIN_AIRPORT"].map(mappings["ORIGIN"])
    data["DEST_DELAY_RATE"] = data["DESTINATION_AIRPORT"].map(mappings["DESTINATION"])

    data["ROUTE_DELAY_RATE"] = data.set_index(
        ["ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]
    ).index.map(mappings["ROUTE"])

    data["AIRLINE_ROUTE_DELAY_RATE"] = data.set_index(
        ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]
    ).index.map(mappings["AIRLINE_ROUTE"])

    data["AIRLINE_HOUR_DELAY_RATE"] = data.set_index(
        ["AIRLINE", "DEP_HOUR"]
    ).index.map(mappings["AIRLINE_HOUR"])

    data["ORIGIN_HOUR_DELAY_RATE"] = data.set_index(
        ["ORIGIN_AIRPORT", "DEP_HOUR"]
    ).index.map(mappings["ORIGIN_HOUR"])

    count_maps = {
        "AIRLINE": ["AIRLINE"],
        "ORIGIN": ["ORIGIN_AIRPORT"],
        "ROUTE": ["ORIGIN_AIRPORT", "DESTINATION_AIRPORT"],
        "AIRLINE_ROUTE": ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"],
    }

    for name, columns in count_maps.items():
        index = data.set_index(columns).index
        data[name + "_HIST_COUNT"] = index.map(mappings[name + "_COUNT"])

    rate_columns = [
        "AIRLINE_DELAY_RATE", "ORIGIN_DELAY_RATE",
        "DEST_DELAY_RATE", "ROUTE_DELAY_RATE",
        "AIRLINE_ROUTE_DELAY_RATE", "AIRLINE_HOUR_DELAY_RATE",
        "ORIGIN_HOUR_DELAY_RATE"
    ]

    count_columns = [
        "AIRLINE_HIST_COUNT", "ORIGIN_HIST_COUNT",
        "ROUTE_HIST_COUNT", "AIRLINE_ROUTE_HIST_COUNT"
    ]

    data[rate_columns] = data[rate_columns].fillna(global_rate)
    data[count_columns] = data[count_columns].fillna(0)

    return data

print("Engineering training features...")
train = add_features(model_training_period)

print("Engineering validation features...")
val = add_features(val_period)

print("Engineering test features...")
test = add_features(test_period)

NEW_FEATURES = FEATURES + [
    "AIRLINE_DELAY_RATE",
    "ORIGIN_DELAY_RATE",
    "DEST_DELAY_RATE",
    "ROUTE_DELAY_RATE",
    "AIRLINE_ROUTE_DELAY_RATE",
    "AIRLINE_HOUR_DELAY_RATE",
    "ORIGIN_HOUR_DELAY_RATE",
    "AIRLINE_HIST_COUNT",
    "ORIGIN_HIST_COUNT",
    "ROUTE_HIST_COUNT",
    "AIRLINE_ROUTE_HIST_COUNT"
]

print("Sampling...")
train = train.sample(n=min(500000, len(train)), random_state=42)
val = val.sample(n=min(100000, len(val)), random_state=42)
test = test.sample(n=min(100000, len(test)), random_state=42)

for data in [train, val, test]:
    data[CAT_COLS] = data[CAT_COLS].astype("category")

# Align categorical levels
for column in CAT_COLS:
    categories = train[column].cat.categories
    val[column] = val[column].astype(str).astype(pd.CategoricalDtype(categories))
    test[column] = test[column].astype(str).astype(pd.CategoricalDtype(categories))

X_train = train[NEW_FEATURES]
y_train = train[TARGET].astype(int)

X_val = val[NEW_FEATURES]
y_val = val[TARGET].astype(int)

X_test = test[NEW_FEATURES]
y_test = test[TARGET].astype(int)

print("Training LightGBM with engineered features...")

model = LGBMClassifier(
    n_estimators=1500,
    learning_rate=0.05,
    num_leaves=31,
    min_child_samples=100,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

model.fit(
    X_train,
    y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[
        early_stopping(100),
        log_evaluation(100)
    ]
)

print("\nEvaluating test set...")
probs = model.predict_proba(X_test)[:, 1]
pred = (probs >= 0.14).astype(int)

print("\n===== FEATURE-ENGINEERED MODEL RESULTS =====")
print("Accuracy:", round(accuracy_score(y_test, pred), 4))
print("Precision:", round(precision_score(y_test, pred, zero_division=0), 4))
print("Recall:", round(recall_score(y_test, pred, zero_division=0), 4))
print("F1:", round(f1_score(y_test, pred, zero_division=0), 4))
print("ROC-AUC:", round(roc_auc_score(y_test, probs), 4))
print("Brier Score:", round(brier_score_loss(y_test, probs), 4))
print("Log Loss:", round(log_loss(y_test, probs), 4))

print("\nActual delay rate:", round(y_test.mean(), 4))
print("Mean predicted probability:", round(probs.mean(), 4))
print("Predicted delayed:", int(pred.sum()))
print("Actual delayed:", int(y_test.sum()))

os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/flightpulse_lightgbm_features.pkl")
joblib.dump(mappings, "models/flightpulse_delay_rate_mappings.pkl")

print("\nFeature-engineered model saved.")
