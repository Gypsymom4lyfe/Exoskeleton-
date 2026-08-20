# Architecture

## Overview

The Exoskeleton telemetry pipeline simulates biometric signals and streams them into an observability stack for analysis and visualization.

## Components

1. **Telemetry Simulator**
   - File: `simulators/physiology_telemetry_generator.py`
   - Responsibility: generate realistic physiological data and POST JSON payloads on an interval.

2. **Telemetry Gateway**
   - Endpoint: configurable via `GATEWAY_URL`
   - Responsibility: receive payloads, validate/transform, and forward to storage.

3. **InfluxDB**
   - URL: `http://localhost:8086`
   - Responsibility: time-series storage for telemetry records.

4. **Grafana**
   - URL: `http://localhost:3000`
   - Responsibility: real-time dashboards and trend visualization.

## Data Flow

1. Simulator generates one payload every 2 seconds.
2. Payload is POSTed to the gateway.
3. Gateway writes point(s) to InfluxDB bucket (`biometrics`).
4. Grafana queries InfluxDB for live dashboard panels.

## Payload Shape

```json
{
  "user_id": "subject_alpha",
  "heart_rate": 78.4,
  "hrv_ms": 49.2,
  "step_count": 3451,
  "spo2": 98.1
}
```

## Simulation Model Notes

- Activity states: `resting`, `walking`, `exertion`
- State changes occur periodically to create realistic variation
- Heart rate transitions smoothly (inertia) instead of instant jumps
- HRV inversely follows heart-rate elevation
- SpO2 remains bounded with slight variance by activity intensity

## Reliability Behaviors

- Request timeout on POST
- Exception handling for network failures
- Continuous loop with configurable interval
