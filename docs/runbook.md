# Runbook

## Prerequisites

- Python 3.9+
- Network access to telemetry gateway
- InfluxDB running (`http://localhost:8086`)
- Grafana running (`http://localhost:3000`)

## Install

```bash
pip install -r requirements.txt
```

## Configure

Optional environment variable:

- `GATEWAY_URL` (default: `http://localhost:8000/api/v1/telemetry`)

**macOS/Linux**
```bash
export GATEWAY_URL="http://localhost:8000/api/v1/telemetry"
```

**Windows (PowerShell)**
```powershell
$env:GATEWAY_URL="http://localhost:8000/api/v1/telemetry"
```

## Start Simulator

```bash
python simulators/physiology_telemetry_generator.py
```

## Validation Checklist

- [ ] Terminal prints payloads every ~2 seconds
- [ ] State transition banner appears periodically
- [ ] InfluxDB receives new points in `biometrics` bucket
- [ ] Grafana panels update for Heart Rate and HRV

## Common Issues

### 1) Connection errors to gateway

**Symptom:**
`[CONNECTION ERROR] Failed to reach telemetry gateway ...`

**Actions:**
1. Verify gateway process is running
2. Verify `GATEWAY_URL` value
3. Confirm local/network firewall rules
4. Check endpoint path `/api/v1/telemetry`

### 2) Non-200/201 gateway responses

**Symptom:**
`[ERROR] Gateway responded with status ...`

**Actions:**
1. Inspect response text in terminal
2. Check gateway logs for schema validation failures
3. Validate JSON fields/types in payload

### 3) No data visible in Grafana

**Actions:**
1. Confirm InfluxDB datasource is healthy
2. Check bucket and query time range
3. Validate panel query uses recent window (e.g., last 5 minutes)

## Stop Procedure

Press `CTRL+C` in the running terminal.
