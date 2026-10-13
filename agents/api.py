"""
FastAPI REST API Server for Kinetic Gfr Dynamic Calculator.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from kinetic_gfr import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Kinetic Gfr Dynamic Calculator API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "kinetic-gfr-dynamic-calculator", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


class KineticGFRRequest(BaseModel):
    steady_state_creatinine: float = Field(gt=0, allow_inf_nan=False)
    baseline_gfr: float = Field(gt=0, allow_inf_nan=False)
    creatinine_1: float = Field(gt=0, allow_inf_nan=False)
    creatinine_2: float = Field(gt=0, allow_inf_nan=False)
    hours: float = Field(gt=0, allow_inf_nan=False)
    max_creatinine_rise_per_day: float = Field(default=1.5, gt=0, allow_inf_nan=False)
    unit: str = "mg/dL"


@app.post("/api/kinetic-gfr")
def api_kinetic_gfr(req: KineticGFRRequest):
    """Clinical-domain calculation only; no task identifiers or PHI."""
    try:
        return calculate_metrics(**req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
