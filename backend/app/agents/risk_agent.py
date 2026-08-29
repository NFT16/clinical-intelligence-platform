
from sqlalchemy.orm import Session

from app.ml import predict


def explain_risk(db: Session, patient_id: str, risk_type: str = "readmission") -> dict:
    if risk_type == "length_of_stay":
        result = predict.predict_length_of_stay(db, patient_id)
        label = "predicted length of stay"
        unit = "days"
    else:
        result = predict.predict_readmission(db, patient_id)
        label = "30-day readmission risk"
        unit = "probability"

    if "error" in result:
        return {
            "answer": f"Could not compute {label}: {result['error']}",
            "evidence_sources": [],
            "confidence": 0.0,
        }

    score_display = f"{result['score']:.0%}" if unit == "probability" else f"{result['score']:.1f} days"
    factors = "; ".join(result["top_factors"])

    answer = (
        f"{label.capitalize()}: {score_display}. "
        f"Top contributing factors (SHAP): {factors}."
    )

    return {
        "answer": answer,
        "evidence_sources": [f"XGBoost {risk_type} model", "SHAP explainability"],
        "confidence": result["confidence"],
    }
