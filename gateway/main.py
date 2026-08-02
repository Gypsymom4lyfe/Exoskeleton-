import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel, Field

app = FastAPI(title="Digital Clone Biological Telemetry Gateway")

INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG", "digital_clone")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "biometrics")

client: Optional[InfluxDBClient] = None
write_api = None


class BiometricPayload(BaseModel):
    user_id: str = Field(default="clone_subject_01", min_length=1)
    heart_rate: float = Field(..., ge=30, le=240, description="BPM")
    hrv_ms: Optional[float] = Field(default=None, ge=0, description="HRV in milliseconds")
    step_count: int = Field(default=0, ge=0)
    spo2: Optional[float] = Field(default=None, ge=70, le=100)


@app.on_event("startup")
def startup_event() -> None:
    global client, write_api
    if not INFLUX_TOKEN:
        return

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


@app.post("/api/v1/telemetry", status_code=status.HTTP_201_CREATED)
def ingest_telemetry(payload: BiometricPayload):
    if write_api is None:
        raise HTTPException(status_code=503, detail="InfluxDB client is not configured")

    try:
        now = datetime.now(timezone.utc)
        point = (
            Point("biometrics")
            .tag("user_id", payload.user_id)
            .field("heart_rate", payload.heart_rate)
            .field("step_count", payload.step_count)
            .time(now)
        )

        if payload.hrv_ms is not None:
            point = point.field("hrv_ms", payload.hrv_ms)
        if payload.spo2 is not None:
            point = point.field("spo2", payload.spo2)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        return {"message": "Telemetry written successfully", "timestamp": now.isoformat()}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to write telemetry")
