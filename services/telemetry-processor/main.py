"""
Telemetry Processor – local aggregation and InfluxDB writer.

Exposes:
  GET  /health              – liveness probe used by Docker health check
  POST /ingest              – accept a normalised telemetry payload, aggregate,
                              and write derived metrics to InfluxDB
"""

import os
from datetime import datetime

from fastapi import FastAPI
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import BaseModel

app = FastAPI(title="Telemetry Processor", version="0.1.0")

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "exoskeleton")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "bodymatrix")


def _influx_write_api():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    return client.write_api(write_options=SYNCHRONOUS)


# ── Health probe ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "service": "telemetry-processor", "timestamp": datetime.utcnow().isoformat()}


# ── Ingest endpoint ────────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    user_id: str
    payload: dict


@app.post("/ingest", tags=["telemetry"])
async def ingest(request: IngestRequest) -> dict:
    """
    Receive a telemetry payload, extract derived metrics (privacy-minimised),
    and write them to InfluxDB.  Raw high-frequency values are NOT forwarded
    beyond this service boundary.
    """
    payload = request.payload
    user_id = request.user_id

    # Extract minimised, derived metrics only
    bpm = payload.get("heart_rate", {}).get("bpm")
    hrv = payload.get("heart_rate", {}).get("hrv_ms")
    step_count = payload.get("movement", {}).get("step_count")
    sleep_score = (payload.get("recovery") or {}).get("sleep_score")

    if INFLUXDB_TOKEN:
        point = (
            Point("body_matrix")
            .tag("user_id", user_id)
        )
        if bpm is not None:
            point = point.field("bpm", float(bpm))
        if hrv is not None:
            point = point.field("hrv_ms", float(hrv))
        if step_count is not None:
            point = point.field("step_count", int(step_count))
        if sleep_score is not None:
            point = point.field("sleep_score", int(sleep_score))

        write_api = _influx_write_api()
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

    return {"status": "ingested", "user_id": user_id, "fields_written": {
        "bpm": bpm, "hrv_ms": hrv, "step_count": step_count, "sleep_score": sleep_score
    }}
