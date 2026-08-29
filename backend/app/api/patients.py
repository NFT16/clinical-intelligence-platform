from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.patient import Patient

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/")
def list_patients(limit: int = 20, db: Session = Depends(get_db)):
    patients = db.query(Patient).limit(limit).all()
    return [
        {
            "id": p.id,
            "name": f"{p.first_name} {p.last_name}",
            "birth_date": p.birth_date,
            "gender": p.gender,
        }
        for p in patients
    ]


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "id": patient.id,
        "name": f"{patient.first_name} {patient.last_name}",
        "birth_date": patient.birth_date,
        "gender": patient.gender,
        "conditions": [c.description for c in patient.conditions],
        "medications": [m.description for m in patient.medications],
        "allergies": [a.description for a in patient.allergies],
    }
