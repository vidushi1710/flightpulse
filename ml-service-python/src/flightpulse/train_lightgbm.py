import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import (
    roc_auc_score, brier_score_loss, log_loss,
    accuracy_score, precision_score, recall_score, f1_score
)

DATA = Path("data/processed/flights_cleaned.csv")
MODEL_PATH = Path("models/flightpulse_lightgbm.pkl")

columns = [
    "FLIGHT_DATE", "MONTH", "DAY_OF_WEEK", "AIRLINE",
    "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
    "SCHEDULED_DEPARTURE", "SCHEDULED_ARRIVAL",
    "DISTANCE", "IS_DELAYED"
]

print("Loading dataset...")
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

train = df[df["FLIGHT_DATE"] < "2015-10-01"]
val = df[
    (df["FLIGHT_DATE"] >= "2015-10-01") &
    (df["FLIGHT_DATE"] < "2015-12-01")
]
test = df[df["FLIGHT_DATE"] >= "2015-12-01"]

print("\nChronological split:")
print("Training:", len(train))
print("Validation:", len(val))
print("Testing:", len(test))

train = train.sample(n=500000, random_state=42)
val = val.sample(n=100000, random_state=42)
test = test.sample(n=100000, random_state=42)

X_train = train[FEATURES]
y_train = train["IS_DELAYED"].astype(int)

X_val = val[FEATURES]
y_val = val["IS_DELAYED"].astype(int)

X_test = test[FEATURES]
y_test = test["IS_DELAYED"].astype(int)

print("\nSample sizes:")
print("Training:", len(train))
print("Validation:", len(val))
print("Testing:", len(test))

print("\nTraining LightGBM...")

model = LGBMClassifier(
    objective="binary",
    n_estimators=1500,
    learning_rate=0.05,
    num_leaves=31,
    max_depth=-1,
    min_child_samples=100,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

model.fit(
    X_train,
    y_train,
    categorical_feature=CATEGORICAL,
    eval_set=[(X_val, y_val)],
    eval_metric="binary_logloss",
    callbacks=[
        early_stopping(100),
        log_evaluation(100)
    ]
)

print("\nGenerating test predictions...")
probs = model.predict_proba(X_test)[:, 1]
preds = (probs >= 0.5).astype(int)

print("\n===== LIGHTGBM TEST RESULTS =====")
print("Accuracy:", round(accuracy_score(y_test, preds), 4))
print("Precision:", round(precision_score(y_test, preds, zero_division=0), 4))
print("Recall:", round(recall_score(y_test, preds, zero_division=0), 4))
print("F1:", round(f1_score(y_test, preds, zero_division=0), 4))
print("ROC-AUC:", round(roc_auc_score(y_test, probs), 4))
print("Brier Score:", round(brier_score_loss(y_test, probs), 4))
print("Log Loss:", round(log_loss(y_test, probs), 4))
print("Actual delay rate:", round(y_test.mean() * 100, 2), "%")
print("Mean predicted probability:", round(probs.mean() * 100, 2), "%")
print("Best iteration:", model.best_iteration_)

test = test.copy()
test["PROBABILITY"] = probs
test["ACTUAL"] = y_test.values
test["BUCKET"] = pd.cut(
    test["PROBABILITY"],
    bins=[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1],
    include_lowest=True
)

print("\n===== PROBABILITY BUCKETS =====")
print(
    test.groupby("BUCKET", observed=False)
    .agg(
        Flights=("ACTUAL", "count"),
        Predicted=("PROBABILITY", "mean"),
        Actual=("ACTUAL", "mean")
    ).to_string()
)

joblib.dump(model, MODEL_PATH)

print("\nModel saved:", MODEL_PATH)
print("LightGBM training complete.")
