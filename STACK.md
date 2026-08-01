# Exoskeleton Telemetry Stack

A local-first, privacy-safe Docker Compose stack that collects biometric
telemetry from wearable devices, processes it locally, stores derived metrics
in InfluxDB, and exposes dashboards through Grafana.

---

## Architecture

```
Wearables / Webhooks
        │
        ▼
┌───────────────────┐   POST /ingest   ┌──────────────────────┐   InfluxDB write
│  webhook-ingestion│ ───────────────► │ telemetry-processor  │ ─────────────────►  InfluxDB (8086)
│  (port 8080)      │                  │  (port 9000)         │                         │
└───────────────────┘                  └──────────────────────┘                         │
                                                                                         ▼
External clients                                                                   Grafana (3000)
        │
        ▼
┌───────────────────┐   POST /ingest
│  fastapi-gateway  │ ───────────────► telemetry-processor
│  (port 8000)      │
└───────────────────┘
```

All services share a private Docker bridge network (`telemetry-net`).
No service is reachable from the internet except through the published ports above.

---

## Services

| Service              | Port | Image / Build              | Role                                                          |
|----------------------|------|----------------------------|---------------------------------------------------------------|
| `fastapi-gateway`    | 8000 | `./services/gateway`       | Public API entrypoint; validates and forwards payloads        |
| `telemetry-processor`| 9000 | `./services/telemetry-processor` | Normalises, aggregates, writes derived metrics to InfluxDB |
| `webhook-ingestion`  | 8080 | `./services/webhook-ingestion` | Receives raw wearable / webhook events; strips raw data    |
| `influxdb`           | 8086 | `influxdb:2.7`             | Time-series storage for biometric metrics                     |
| `grafana`            | 3000 | `grafana/grafana:latest`   | Dashboard and visualisation layer                             |

---

## Quick Start

### 1 – Prerequisites

- Docker ≥ 24 with the Compose plugin (v2)
- `curl` available locally for smoke tests

### 2 – Configure secrets

```bash
cp .env.example .env
# Edit .env and replace every `change-me-*` value with strong secrets
```

> **Never commit `.env` to version control.**  
> `.gitignore` already excludes it.

### 3 – Build and start

```bash
docker compose up --build
```

Wait until all health checks pass (watch with `docker compose ps`).

### 4 – Smoke test

```bash
# Gateway liveness
curl http://localhost:8000/health

# Telemetry processor liveness
curl http://localhost:9000/health

# Webhook ingestion liveness
curl http://localhost:8080/health

# InfluxDB health
curl http://localhost:8086/health

# Grafana health
curl http://localhost:3000/api/health
```

### 5 – Open Grafana

Navigate to <http://localhost:3000> and log in with the credentials set in `.env`.

---

## Privacy & Security Notes

- **Local-first**: raw wearable payloads never leave the `webhook-ingestion`
  service boundary; only a privacy-minimised envelope is forwarded onward.
- **Data minimisation**: the telemetry processor writes only derived/aggregated
  metrics to InfluxDB — not raw high-frequency streams.
- **No hardcoded secrets**: all credentials are provided via `.env` (or your
  preferred secrets manager). See `.env.example` for the full list.
- **Isolated network**: all inter-service traffic stays on the private
  `telemetry-net` bridge — services are not reachable from other Docker networks
  or the host except on the explicitly published ports.

---

## Follow-up Work

- [ ] Add Grafana provisioned datasource and dashboard JSON under `grafana/provisioning/`
- [ ] Add rate limiting and authentication middleware to the FastAPI gateway
- [ ] Implement a real wearable adapter (e.g., Apple Health, Garmin, Oura) in `webhook-ingestion`
- [ ] Add rolling-window aggregation logic to `telemetry-processor`
- [ ] Integrate HashiCorp Vault or OS Keychain for biometric token storage
- [ ] Add structured logging and an optional audit trail for data-access events
- [ ] Write integration tests for each service's `/health` and core endpoints
