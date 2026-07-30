## Telemetry Simulator

This project includes a physiological telemetry simulator that streams synthetic biometric data to a telemetry gateway.

### File
- `simulators/physiology_telemetry_generator.py`

### What it Simulates
- Heart Rate (BPM)
- HRV (ms)
- Step Count
- SpO2 (%)

The simulator automatically transitions between activity states:
- `RESTING`
- `WALKING`
- `EXERTION`

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

> `requirements.txt` includes:
> - `requests`

---

## Run

From the repository root:

```bash
python simulators/physiology_telemetry_generator.py
```

Optional: override the telemetry gateway URL (default is `http://localhost:8000/api/v1/telemetry`)

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

---

## How to Validate

1. **Terminal Stream**  
   The script prints live biometric telemetry payloads continuously and shows state transitions:
   - `RESTING`
   - `WALKING`
   - `EXERTION`

2. **InfluxDB Dashboard**  
   Open: http://localhost:8086  
   Confirm live telemetry points are being written to the **biometrics** bucket.

3. **Grafana Real-time Plotting**  
   Open: http://localhost:3000  
   Build or open dashboard panels for:
   - Heart Rate
   - HRV  
   Confirm continuous real-time updates.

---

## Notes

- Default send interval is every **2 seconds**.
- Stop the stream with `CTRL+C`.
