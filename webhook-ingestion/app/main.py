import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Telemetry Webhook Ingestion")

TELEMETRY_GATEWAY_URL = os.getenv("TELEMETRY_GATEWAY_URL", "http://telemetry_gateway:8000/api/v1/telemetry")


class TelemetryWebhookPayload(BaseModel):
    user_id: str = Field(default="clone_subject_01", min_length=1)
    heart_rate: float = Field(..., ge=30, le=240)
    hrv_ms: Optional[float] = Field(default=None, ge=0)
    step_count: int = Field(default=0, ge=0)
    spo2: Optional[float] = Field(default=None, ge=70, le=100)
    prompt_context: Optional[str] = Field(default=None, max_length=2000)


@app.get("/health")
def health_check():
    return {"status": "online", "gateway_url": TELEMETRY_GATEWAY_URL}


@app.post("/webhook/telemetry", status_code=status.HTTP_202_ACCEPTED)
def ingest_webhook(payload: TelemetryWebhookPayload):
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(TELEMETRY_GATEWAY_URL, json=payload.model_dump())
            response.raise_for_status()
        return {
            "message": "Webhook accepted",
            "forwarded_at": datetime.now(timezone.utc).isoformat(),
        }
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to forward webhook telemetry")
