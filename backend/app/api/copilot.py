from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.agents.orchestrator import run_copilot

router = APIRouter(prefix="/copilot", tags=["copilot"])


class CopilotRequest(BaseModel):
    patient_id: str
    question: str


class CopilotResponse(BaseModel):
    answer: str
    evidence_sources: list[str]
    confidence: float


@router.post("/ask", response_model=CopilotResponse)
def ask_copilot(request: CopilotRequest, db: Session = Depends(get_db)):
    result = run_copilot(db, request.patient_id, request.question)
    return CopilotResponse(**result)
