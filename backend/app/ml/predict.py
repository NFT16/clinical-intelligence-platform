"""
Loads trained models (from train.py) and runs predictions with SHAP-based
explanations for a given patient's most recent encounter.
"""

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.ml.features import build_feature_table
from app.ml.train import ARTIFACTS_DIR, _prepare_X

_cache: dict = {}


def _load(name: str):
    if name not in _cache:
        try:
            _cache[name] = joblib.load(f"{ARTIFACTS_DIR}/{name}.joblib")
        except FileNotFoundError:
            return None
    return _cache[name]


def _latest_encounter_features(db: Session, patient_id: str) -> pd.DataFrame | None:
    df = build_feature_table(db)
    patient_rows = df[df["patient_id"] == patient_id]
    if patient_rows.empty:
        return None
    return patient_rows.iloc[[-1]]  # most recent encounter


def predict_readmission(db: Session, patient_id: str) -> dict:
    row = _latest_encounter_features(db, patient_id)
    if row is None:
        return {"error": "no encounters found for this patient"}

    model = _load("readmission_model")
    explainer = _load("readmission_explainer")
    if model is None or explainer is None:
        return {"error": "readmission model not trained yet — run app/ml/train.py"}

    X = _prepare_X(row)
    score = float(model.predict_proba(X)[0][1])

    shap_values = explainer.shap_values(X)
    contributions = list(zip(X.columns, shap_values[0]))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)
    top_factors = [f"{name} (impact: {val:+.3f})" for name, val in contributions[:3]]

    return {
        "score": score,
        "unit": "probability",
        "confidence": max(score, 1 - score),  # distance from 0.5 as a rough proxy
        "top_factors": top_factors,
    }


def predict_length_of_stay(db: Session, patient_id: str) -> dict:
    row = _latest_encounter_features(db, patient_id)
    if row is None:
        return {"error": "no encounters found for this patient"}

    model = _load("los_model")
    explainer = _load("los_explainer")
    if model is None or explainer is None:
        return {"error": "length-of-stay model not trained yet — run app/ml/train.py"}

    X = _prepare_X(row)
    predicted_days = float(model.predict(X)[0])

    shap_values = explainer.shap_values(X)
    contributions = list(zip(X.columns, shap_values[0]))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)
    top_factors = [f"{name} (impact: {val:+.2f} days)" for name, val in contributions[:3]]

    return {
        "score": predicted_days,
        "unit": "days",
        "confidence": 0.7,  # regression models don't have a natural confidence score;
                             # for a real deliverable, use prediction interval width instead
        "top_factors": top_factors,
    }
