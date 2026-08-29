from fastapi import FastAPI

from app.api import patients, risk, copilot, medication, hospital_ops, alerts

app = FastAPI(
    title="Clinical Intelligence Platform",
    description="AI-047 case study",
    version="0.2.0",
)

app.include_router(patients.router)
app.include_router(risk.router)
app.include_router(copilot.router)
app.include_router(medication.router)
app.include_router(hospital_ops.router)
app.include_router(alerts.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
