from fastapi import APIRouter

from app.services.hospital_ops_simulator import get_hospital_ops_summary

router = APIRouter(prefix="/hospital-ops", tags=["hospital-operations"])


@router.get("/summary")
def hospital_ops_summary():
    return get_hospital_ops_summary()
