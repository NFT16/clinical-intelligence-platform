from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.ml import predict

router = APIRouter(prefix="/risk", tags=["risk"])


class RiskResponse(BaseModel):
    patient_id: str
    risk_type: str
    score: float
    unit: str
    confidence: float
    top_factors: list[str]


@router.get("/{patient_id}/readmission", response_model=RiskResponse)
def get_readmission_risk(patient_id: str, db: Session = Depends(get_db)):
    result = predict.predict_readmission(db, patient_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return RiskResponse(patient_id=patient_id, risk_type="readmission", **result)


@router.get("/{patient_id}/length-of-stay", response_model=RiskResponse)
def get_los_prediction(patient_id: str, db: Session = Depends(get_db)):
    result = predict.predict_length_of_stay(db, patient_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return RiskResponse(patient_id=patient_id, risk_type="length_of_stay", **result)


@router.get("/{patient_id}/all", response_model=list[RiskResponse])
def get_all_risks(patient_id: str, db: Session = Depends(get_db)):
    """Convenience endpoint — used by the dashboard and by the copilot's risk agent."""
    responses = []
    for risk_type, fn in [
        ("readmission", predict.predict_readmission),
        ("length_of_stay", predict.predict_length_of_stay),
    ]:
        result = fn(db, patient_id)
        if "error" not in result:
            responses.append(RiskResponse(patient_id=patient_id, risk_type=risk_type, **result))
    return responses
