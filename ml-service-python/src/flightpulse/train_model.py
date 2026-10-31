from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "flights_cleaned.csv"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_FILE = MODEL_DIR / "flight_delay_model.pkl"

TRAIN_SAMPLE_SIZE = 500_000
VALIDATION_SAMPLE_SIZE = 100_000
TEST_SAMPLE_SIZE = 100_000
RANDOM_STATE = 42


def load_data():
    print("Loading cleaned flight dataset...")
    required_columns = [
        "FLIGHT_DATE", "MONTH", "DAY_OF_WEEK", "AIRLINE",
        "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "SCHEDULED_ARRIVAL",
        "DISTANCE", "IS_DELAYED",
    ]
    flights = pd.read_csv(
        DATA_FILE,
        usecols=required_columns,
        dtype={
            "AIRLINE": "string",
            "ORIGIN_AIRPORT": "string",
            "DESTINATION_AIRPORT": "string",
        },
    )
    flights["FLIGHT_DATE"] = pd.to_datetime(flights["FLIGHT_DATE"])
    print("Loaded records:", len(flights))
    return flights


def prepare_features(flights):
    flights = flights.copy()
    flights["DEP_HOUR"] = flights["SCHEDULED_DEPARTURE"] // 100
    flights["ARR_HOUR"] = flights["SCHEDULED_ARRIVAL"] // 100
    flights.loc[flights["DEP_HOUR"] == 24, "DEP_HOUR"] = 0
    flights.loc[flights["ARR_HOUR"] == 24, "ARR_HOUR"] = 0

    numeric_features = [
        "MONTH", "DAY_OF_WEEK", "DEP_HOUR", "ARR_HOUR", "DISTANCE",
    ]
    categorical_features = [
        "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
    ]
    feature_columns = numeric_features + categorical_features
    return (
        flights[feature_columns],
        flights["IS_DELAYED"].astype(int),
        numeric_features,
        categorical_features,
    )


def split_data(flights):
    train = flights[flights["FLIGHT_DATE"] < "2015-10-01"].copy()
    validation = flights[
        (flights["FLIGHT_DATE"] >= "2015-10-01")
        & (flights["FLIGHT_DATE"] < "2015-12-01")
    ].copy()
    test = flights[flights["FLIGHT_DATE"] >= "2015-12-01"].copy()

    print("\nChronological split:")
    print("Training:", len(train))
    print("Validation:", len(validation))
    print("Testing:", len(test))

    train = train.sample(
        n=min(TRAIN_SAMPLE_SIZE, len(train)), random_state=RANDOM_STATE
    )
    validation = validation.sample(
        n=min(VALIDATION_SAMPLE_SIZE, len(validation)),
        random_state=RANDOM_STATE,
    )
    test = test.sample(
        n=min(TEST_SAMPLE_SIZE, len(test)), random_state=RANDOM_STATE
    )

    print("\nSample sizes:")
    print("Training:", len(train))
    print("Validation:", len(validation))
    print("Testing:", len(test))
    return train, validation, test


def build_model(numeric_features, categorical_features):
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                categorical_features,
            ),
        ]
    )
    classifier = SGDClassifier(
        loss="log_loss",
        class_weight="balanced",
        max_iter=10,
        tol=0.001,
        random_state=RANDOM_STATE,
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )


def evaluate_model(model, X, y, dataset_name):
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]
    print(f"\n{dataset_name} RESULTS")
    print("-" * 40)
    print("Accuracy:", round(accuracy_score(y, predictions), 4))
    print("Precision:", round(precision_score(y, predictions, zero_division=0), 4))
    print("Recall:", round(recall_score(y, predictions, zero_division=0), 4))
    print("F1 Score:", round(f1_score(y, predictions, zero_division=0), 4))
    print("ROC-AUC:", round(roc_auc_score(y, probabilities), 4))
    print("\nClassification Report:")
    print(classification_report(y, predictions, zero_division=0))


def main():
    flights = load_data()
    train, validation, test = split_data(flights)

    X_train, y_train, numeric_features, categorical_features = prepare_features(train)
    X_validation, y_validation, _, _ = prepare_features(validation)
    X_test, y_test, _, _ = prepare_features(test)

    print("\nBuilding Logistic Regression baseline...")
    model = build_model(numeric_features, categorical_features)
    print("\nTraining model...")
    model.fit(X_train, y_train)
    print("\nTraining completed!")

    evaluate_model(model, X_validation, y_validation, "VALIDATION")
    evaluate_model(model, X_test, y_test, "TEST")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print("\nModel saved successfully!")
    print("Model location:", MODEL_FILE)


if __name__ == "__main__":
    main()
