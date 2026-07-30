import os
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Digital Clone Biological Telemetry Gateway")

TELEMETRY_PROCESSOR_URL = os.getenv("TELEMETRY_PROCESSOR_URL", "http://telemetry_processor:9000")
PROCESSOR_ENDPOINT = f"{TELEMETRY_PROCESSOR_URL.rstrip('/')}/process"


class BiometricPayload(BaseModel):
    user_id: str = Field(default="clone_subject_01", min_length=1)
    heart_rate: float = Field(..., ge=30, le=240, description="BPM")
    hrv_ms: Optional[float] = Field(default=None, ge=0, description="HRV in milliseconds")
    step_count: int = Field(default=0, ge=0)
    spo2: Optional[float] = Field(default=None, ge=70, le=100)
    prompt_context: Optional[str] = Field(default=None, max_length=2000)


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_\-]{20,}\b")


def _sanitize_prompt(prompt_context: Optional[str]) -> Optional[str]:
    if not prompt_context:
        return None

    sanitized = EMAIL_PATTERN.sub("[redacted-email]", prompt_context)
    sanitized = TOKEN_PATTERN.sub("[redacted-token]", sanitized)
    return sanitized[:512]


@app.get("/health")
def health_check():
    return {"status": "online", "processor_endpoint": PROCESSOR_ENDPOINT}


@app.post("/api/v1/telemetry", status_code=status.HTTP_201_CREATED)
def ingest_telemetry(payload: BiometricPayload):
    outbound_payload = payload.model_dump()
    outbound_payload["prompt_context"] = _sanitize_prompt(payload.prompt_context)

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(PROCESSOR_ENDPOINT, json=outbound_payload)
            response.raise_for_status()
        return {
            "message": "Telemetry written successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "privacy_filters_applied": payload.prompt_context is not None,
        }
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to forward telemetry")
