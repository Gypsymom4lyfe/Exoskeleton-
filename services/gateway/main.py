"""
FastAPI Gateway – public API entrypoint.

Exposes:
  GET  /health              – liveness probe used by Docker health check
  POST /telemetry           – forward an enriched payload to the telemetry processor
"""

import os
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Exoskeleton Gateway", version="0.1.0")

PROCESSOR_URL = os.getenv("TELEMETRY_PROCESSOR_URL", "http://telemetry-processor:9000")


# ── Health probe ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "service": "fastapi-gateway", "timestamp": datetime.utcnow().isoformat()}


# ── Telemetry forwarding ───────────────────────────────────────────────────────
class TelemetryRequest(BaseModel):
    user_id: str
    payload: dict


@app.post("/telemetry", tags=["telemetry"])
async def forward_telemetry(request: TelemetryRequest) -> dict:
    """
    Accept a normalised telemetry payload from a client and forward it to the
    local telemetry processor for aggregation and storage.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{PROCESSOR_URL}/ingest",
                json=request.model_dump(),
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc)) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Processor unreachable: {exc}") from exc

    return {"status": "forwarded", "processor_response": response.json()}
