
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.patient import Patient, LabResult
from app.services import medication_rules
from app.ml import predict

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Simple reference ranges for a few common labs — enough for a demo.
NORMAL_RANGES = {
    "glucose": (70, 140),
    "potassium": (3.5, 5.0),
    "creatinine": (0.6, 1.3),
    "white blood cells": (4.0, 11.0),
    "hemoglobin": (12.0, 17.0),
}


def _lab_alerts(patient: Patient) -> list[dict]:
    findings = []
    for lab in patient.lab_results:
        if lab.value is None:
            continue
        desc = lab.description.lower()
        for key, (low, high) in NORMAL_RANGES.items():
            if key in desc and not (low <= lab.value <= high):
                findings.append({
                    "type": "critical_lab",
                    "severity": "high",
                    "detail": f"{lab.description} = {lab.value} {lab.unit or ''} (normal: {low}-{high})",
                })
    return findings


@router.get("/{patient_id}")
def get_patient_alerts(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    alerts = []
    alerts += medication_rules.run_all_checks(patient)
    alerts += _lab_alerts(patient)

    readmission = predict.predict_readmission(db, patient_id)
    if "error" not in readmission and readmission["score"] > 0.6:
        alerts.append({
            "type": "high_risk_patient",
            "severity": "high",
            "detail": f"Readmission risk {readmission['score']:.0%} — above threshold.",
        })

    return {"patient_id": patient_id, "alert_count": len(alerts), "alerts": alerts}


@router.get("/")
def get_all_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Hospital-wide feed for the Alert Center / Executive Dashboard tile."""
    patients = db.query(Patient).limit(limit).all()
    feed = []
    for p in patients:
        result = get_patient_alerts(p.id, db)
        if result["alert_count"] > 0:
            feed.append(result)
    return {"patients_with_alerts": len(feed), "feed": feed}
