## Exoskeleton Telemetry Project

Exoskeleton is a biometric telemetry simulation and streaming project designed to generate realistic physiological signals and send them to a telemetry gateway for ingestion, storage, and visualization.

## Current Scope

- Simulate biological metrics in real time:
  - Heart Rate (BPM)
  - HRV (ms)
  - Step Count
  - SpO2 (%)
- Stream telemetry payloads to a configurable gateway endpoint
- Validate end-to-end flow in InfluxDB and Grafana
- Run a local telemetry stack with gateway, processor, webhook ingestion, InfluxDB, and Grafana

## Repository Structure

- `simulators/physiology_telemetry_generator.py` — main telemetry simulator
- `requirements.txt` — Python dependencies
- `docs/architecture.md` — architecture and data flow
- `docs/runbook.md` — run/validate/troubleshooting guide
- `docs/ideas.md` — idea backlog and roadmap notes
- `CHANGELOG.md` — release and change history
- `docker-compose.yml` — local telemetry stack
- `gateway/` — privacy-safe FastAPI telemetry ingress
- `telemetry-processor/` — local processor writing normalized metrics to InfluxDB
- `webhook-ingestion/` — webhook entrypoint forwarding to gateway
- `grafana/provisioning/datasources/influxdb.yml` — Grafana datasource provisioning

## Setup

Install simulator dependencies from repository root:

```bash
pip install -r requirements.txt
```

For local stack configuration, copy `.env.example` to `.env` and set secure local values.

## Run

Run the telemetry simulator:

```bash
python simulators/physiology_telemetry_generator.py
```

Optional environment variable override for gateway:

**macOS/Linux**
```bash
export GATEWAY_URL="http://localhost:8000/api/v1/telemetry"
python simulators/physiology_telemetry_generator.py
```

**Windows (PowerShell)**
```powershell
$env:GATEWAY_URL="http://localhost:8000/api/v1/telemetry"
python simulators/physiology_telemetry_generator.py
```

Run the local telemetry stack:

```bash
docker compose up --build -d
```

## Validation

1. **Terminal Stream**
   - Verify continuous payload output
   - Confirm state transitions appear (`RESTING`, `WALKING`, `EXERTION`)
2. **Gateway Health**
   - Open http://localhost:8000/health
   - Confirm gateway is online
3. **InfluxDB**
   - Open http://localhost:8086
   - Confirm new points are written to the biometrics bucket
4. **Grafana**
   - Open http://localhost:3000
   - Confirm Heart Rate and HRV panels update in real time

## Notes

- Default post interval is 2 seconds
- Stop stream with `CTRL+C`
