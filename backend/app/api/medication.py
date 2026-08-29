from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.patient import Patient
from app.services import medication_rules

router = APIRouter(prefix="/medication", tags=["medication-safety"])


@router.get("/{patient_id}/conflicts")
def get_conflicts(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    findings = medication_rules.run_all_checks(patient)
    return {
        "patient_id": patient_id,
        "conflict_count": len(findings),
        "conflicts": findings,
    }
