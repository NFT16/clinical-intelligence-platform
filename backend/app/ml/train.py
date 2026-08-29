"""
Trains two models on the feature table from features.py:
  1. Readmission risk  — classification (XGBoost)
  2. Length of stay    — regression (XGBoost)
"""

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, mean_absolute_error
from xgboost import XGBClassifier, XGBRegressor

from app.db.postgres import SessionLocal
from app.ml.features import build_feature_table

ARTIFACTS_DIR = "app/ml/artifacts"
FEATURE_COLUMNS = [
    "age", "prior_condition_count", "prior_medication_count",
    "prior_encounter_count", "days_since_last_encounter",
    "gender_M", "encounter_type_inpatient", "encounter_type_emergency",
]


def _prepare_X(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["gender_M"] = (df["gender"] == "M").astype(int)
    df["encounter_type_inpatient"] = (df["encounter_type"] == "inpatient").astype(int)
    df["encounter_type_emergency"] = (df["encounter_type"] == "emergency").astype(int)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
    return df[FEATURE_COLUMNS].fillna(0)


def train_readmission_model(df: pd.DataFrame):
    X = _prepare_X(df)
    y = df["readmitted_30d"]

    if len(df) < 10:
        print(
            f"SKIPPED readmission model: only {len(df)} encounters available, "
            "need at least 10 to do a train/test split. Generate more Synthea "
            "patients first."
        )
        return None

    if y.sum() < 10:
        print(
            f"WARNING: only {y.sum()} positive readmission cases in the data. "
            "Model quality will be poor. Generate more Synthea patients "
            "(try -p 1000+) to get enough positive examples."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 5 else None
    )
    model = XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        eval_metric="logloss", random_state=42,
    )
    model.fit(X_train, y_train)

    if len(y_test.unique()) > 1:
        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        print(f"Readmission model AUC: {auc:.3f}")
    else:
        print("Readmission model: test set has only one class, skipping AUC.")

    joblib.dump(model, f"{ARTIFACTS_DIR}/readmission_model.joblib")

    explainer = shap.TreeExplainer(model)
    joblib.dump(explainer, f"{ARTIFACTS_DIR}/readmission_explainer.joblib")
    return model


def train_los_model(df: pd.DataFrame):
    df = df.dropna(subset=["length_of_stay_days"])

    if len(df) < 10:
        print(
            f"SKIPPED length-of-stay model: only {len(df)} usable encounters, "
            "need at least 10. Generate more Synthea patients first."
        )
        return None

    X = _prepare_X(df)
    y = df["length_of_stay_days"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = XGBRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42,
    )
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"Length-of-stay model MAE: {mae:.2f} days")

    joblib.dump(model, f"{ARTIFACTS_DIR}/los_model.joblib")

    explainer = shap.TreeExplainer(model)
    joblib.dump(explainer, f"{ARTIFACTS_DIR}/los_explainer.joblib")
    return model


def main():
    import os
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    db = SessionLocal()
    try:
        df = build_feature_table(db)
        print(f"Built feature table: {len(df)} encounters")

        if len(df) < 50:
            print(
                "WARNING: fewer than 50 encounters found. Generate more "
                "Synthea patients before training — with only a handful of "
                "encounters both models will be near-meaningless."
            )

        train_readmission_model(df)
        train_los_model(df)

        joblib.dump(FEATURE_COLUMNS, f"{ARTIFACTS_DIR}/feature_columns.joblib")
        print("Training complete. Artifacts saved to", ARTIFACTS_DIR)
    finally:
        db.close()


if __name__ == "__main__":
    main()
