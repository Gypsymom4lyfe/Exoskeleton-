"""
Webhook Ingestion Service – receives raw wearable / third-party webhook payloads.

Exposes:
  GET  /health              – liveness probe used by Docker health check
  POST /webhook             – accept a raw wearable payload, validate, and
                              forward a normalised envelope to the telemetry processor
"""

import os
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(title="Webhook Ingestion", version="0.1.0")

PROCESSOR_URL = os.getenv("TELEMETRY_PROCESSOR_URL", "http://telemetry-processor:9000")


# ── Health probe ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "service": "webhook-ingestion", "timestamp": datetime.utcnow().isoformat()}


# ── Webhook endpoint ───────────────────────────────────────────────────────────
class WearableWebhookPayload(BaseModel):
    """
    Minimal common envelope accepted from wearable device webhooks.
    Extend fields as required for each device integration.
    """
    user_id: str = Field(..., min_length=1)
    source: str = Field(default="unknown", description="Device or platform identifier")
    timestamp: datetime
    raw: dict = Field(default_factory=dict, description="Raw device payload; kept local, not forwarded")


@app.post("/webhook", tags=["ingest"])
async def receive_webhook(payload: WearableWebhookPayload) -> dict:
    """
    Accept a raw wearable webhook.  Only a privacy-minimised normalised envelope
    is forwarded to the telemetry processor; the raw payload stays within this
    service boundary.
    """
    # Build a minimal normalised envelope – raw fields are stripped here
    normalised = {
        "user_id": payload.user_id,
        "payload": {
            "timestamp": payload.timestamp.isoformat(),
            "source": payload.source,
            # Downstream services receive only what they need
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{PROCESSOR_URL}/ingest", json=normalised)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Processor unreachable: {exc}") from exc

    return {"status": "accepted", "forwarded_to": PROCESSOR_URL}
