import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel, Field

app = FastAPI(title="Local Telemetry Processor")

INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG", "digital_clone")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "biometrics")
TELEMETRY_MEASUREMENT = os.getenv("TELEMETRY_MEASUREMENT", "biometrics")

client = None
write_api = None


class ProcessorTelemetryPayload(BaseModel):
    user_id: str = Field(default="clone_subject_01", min_length=1)
    heart_rate: float = Field(..., ge=30, le=240)
    hrv_ms: Optional[float] = Field(default=None, ge=0)
    step_count: int = Field(default=0, ge=0)
    spo2: Optional[float] = Field(default=None, ge=70, le=100)
    prompt_context: Optional[str] = Field(default=None, max_length=512)


def _safe_user_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]


@app.on_event("startup")
def startup_event() -> None:
    global client, write_api
    if not INFLUX_TOKEN:
        raise RuntimeError("INFLUX_TOKEN is required")

    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)


@app.on_event("shutdown")
def shutdown_event() -> None:
    global client
    if client is not None:
        client.close()


@app.get("/health")
def health_check():
    if client is None:
        return {"status": "degraded", "influx_connected": False}

    try:
        return {"status": "online", "influx_connected": client.ping()}
    except Exception:
        return {"status": "degraded", "influx_connected": False}


@app.post("/process", status_code=status.HTTP_201_CREATED)
def process_telemetry(payload: ProcessorTelemetryPayload):
    if write_api is None:
        raise HTTPException(status_code=503, detail="Telemetry processor is not ready")

    try:
        point = (
            Point(TELEMETRY_MEASUREMENT)
            .tag("user_hash", _safe_user_hash(payload.user_id))
            .field("heart_rate", payload.heart_rate)
            .field("step_count", payload.step_count)
            .field("prompt_present", int(payload.prompt_context is not None))
            .field("prompt_length", len(payload.prompt_context or ""))
            .time(datetime.now(timezone.utc))
        )

        if payload.hrv_ms is not None:
            point = point.field("hrv_ms", payload.hrv_ms)
        if payload.spo2 is not None:
            point = point.field("spo2", payload.spo2)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return {
            "message": "Telemetry written successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to write telemetry")
