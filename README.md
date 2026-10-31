# ✈️ FlightPulse

### Flight Delay & Route Risk Prediction System

FlightPulse is a student project exploring flight-delay prediction and route-risk analytics using historical flight data.

**Current implementation:** a reproducible Python cleaning pipeline, a baseline delay classifier, and validation-based threshold selection. The Java Spring Boot backend, React frontend, PostgreSQL integration, live prediction API, and delay-duration regression are planned components and are not yet implemented.

## Dataset

- Source: Kaggle's 2015 Flight Delays and Cancellations dataset (U.S. DOT/BTS data).
- Raw records: 5,819,079.
- Selected columns: 13.
- Cleaned records: 5,714,005.
- Cancelled and diverted flights are excluded.
- Target: `IS_DELAYED = 1` when `ARRIVAL_DELAY >= 15` minutes; otherwise `0`.
- Cleaned target distribution: 4,650,566 not delayed; 1,063,439 delayed (18.61%).

The dataset covers **2015 only**. Results are a historical research baseline and must not be presented as current operational flight guidance.

## Current Python implementation

Located in `ml-service-python/src/flightpulse/`:

- `data_pipeline.py`: loads the raw CSV, cleans records, engineers date/departure-hour fields, creates the classification target, and writes the processed CSV.
- `train_model.py`: creates chronological train/validation/test partitions, trains a baseline SGD logistic classifier, evaluates it, and saves the model locally.
- `tune_threshold.py`: chooses a classification threshold using validation F1 and evaluates that threshold on the held-out test sample.

The model uses scheduled information, airline, origin/destination, and distance. It does **not** use actual `ARRIVAL_DELAY` as a predictor, avoiding direct target leakage.

### Baseline experiment

The initial experiment sampled 500,000 training rows, 100,000 validation rows, and 100,000 December 2015 test rows.

At the default 0.50 threshold, December test metrics were:

| Metric | Result |
|---|---:|
| Accuracy | 0.6961 |
| Precision | 0.2811 |
| Recall | 0.3051 |
| F1 | 0.2926 |
| ROC-AUC | 0.6018 |

Validation threshold tuning selected 0.35 by validation F1. On the held-out test sample at 0.35:

| Metric | Result |
|---|---:|
| Accuracy | 0.5218 |
| Precision | 0.2513 |
| Recall | 0.6680 |
| F1 | 0.3653 |
| ROC-AUC | 0.6018 |

Threshold tuning changes the precision/recall trade-off; it does not improve the model's ranking ability (ROC-AUC). These results show that the current baseline is **not yet sufficiently accurate or discriminative for real-world use**. Further feature engineering, stronger models, calibration, broader time-based validation, and external/current data are required.

## Run locally

From the repository root:

```bash
cd ml-service-python
python3 -m pip install pandas scikit-learn joblib
python3 -m src.flightpulse.data_pipeline
python3 -m src.flightpulse.train_model
python3 -m src.flightpulse.tune_threshold
```

Place the original dataset at `ml-service-python/data/raw/flights.csv` before running the pipeline.

The raw/processed CSV files and locally generated model artifacts are intentionally excluded from Git. Re-running the scripts locally generates them.

## Planned architecture

- **Frontend:** React dashboard
- **Backend:** Java + Spring Boot REST API
- **ML:** Python, Pandas, scikit-learn
- **Database:** PostgreSQL

These components will be integrated after the prediction model is improved and its evaluation is defensible.
