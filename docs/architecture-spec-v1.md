# Edge-Orchestrated Rail Automation & Animatronic Diagnostics Platform (ERADP)

## 1) System Scope & Objectives

**System Name:** Edge-Orchestrated Rail Automation & Animatronic Diagnostics Platform (ERADP)

**Primary goals**
- Deterministic response to train/track/environment triggers
- Safe automation of physical and kinetic subsystems
- Human-legible physical status indication
- Graceful degradation and mechanical fail-safe behavior under faults/power loss

**Non-goals**
- Full autonomous train driving logic (outside this scope)
- Cloud-dependent control loops (cloud is advisory only)

## 2) Control Architecture (Layered)

## L0 — Safety & Interlock Layer (Hard Real-Time)
**Technology:** Safety PLC / safety MCU, hardwired relays, deterministic fieldbus  
**Cycle target:** 5–10 ms  
**Authority:** Absolute (can always inhibit L1/L2)

**Responsibilities**
- Travel-state interlock (no external motion during active traction/brake travel state)
- E-stop handling
- Door/service access safety gating
- Actuator enable/inhibit lines
- Safe-state enforcement on power loss/comms loss

## L1 — Mission & Edge Orchestration Layer
**Technology:** Industrial edge controller(s), RTOS/Linux RT, local broker  
**Cycle target:** 20–100 ms decision windows  
**Authority:** Executes ops only if L0 permits

**Responsibilities**
- Event correlation and rule execution
- Docking/siding sequencing
- Thermal and power balancing logic
- Perimeter response policy selection
- Diagnostics aggregation and fault classification

## L2 — Interaction & Animatronic HMI Layer
**Technology:** MCU clusters for kinetic indicators, lighting, acoustic controllers  
**Cycle target:** 50–500 ms (non-safety)  
**Authority:** Cosmetic/assistive actions only; all gated by L0/L1

**Responsibilities**
- Physical gauge/arms/indicators
- Maintenance inspection rigs
- Community-facing low-noise status signaling
- Local warning choreography

## 3) Network & Data Plane

## 3.1 Dual-Bus Pattern

**A) Safety Bus (deterministic, isolated)**
- Signals: brake state, traction state, E-stop, interlock status, door state, actuator permits
- Allowed publishers/subscribers strictly whitelisted
- No internet/cloud dependency

**B) Telemetry/Event Bus (high-throughput)**
- Sensors: vibration, thermal, acoustic, proximity, radar/optical
- Event topics for orchestration and observability
- Can bridge to historian/cloud asynchronously (read-mostly)

## 3.2 Time Sync & Ordering
- PTP (preferred) or equivalent sub-ms local sync
- Every message stamped with:
  - `event_time` (source)
  - `ingest_time` (node)
  - `sequence_id` (per publisher)
- L1 correlation uses bounded out-of-order window (e.g., 200 ms)

## 4) Canonical State Machine (Global)

**States**
1. `TRAVEL`
2. `APPROACH`
3. `DOCKING`
4. `STATIONARY_SERVICE`
5. `MAINTENANCE`
6. `FAULT_SAFE`

**State authority**
- L0 can force transition to `FAULT_SAFE` anytime
- L1 requests transitions; L0 validates safety predicates

### 4.1 State Entry Predicates (examples)
- `TRAVEL`: traction active OR brake release + speed > threshold
- `DOCKING`: speed < docking threshold, target lock acquired
- `STATIONARY_SERVICE`: speed=0, brakes locked, traction disabled
- `MAINTENANCE`: stationary + keyed authorization + service doors status valid
- `FAULT_SAFE`: E-stop OR critical fault OR power anomaly severe

## 5) Event Taxonomy & Contract

Each event includes:
- `event_id`, `event_type`, `priority`, `source_id`, `event_time`
- `state_context`
- `confidence` (for inferred sensor events)
- `ttl_ms`
- `safety_impact` = `NONE | LOW | HIGH | CRITICAL`

**Priority classes**
- P0: Safety critical (hard-preemptive)
- P1: Operational critical
- P2: Diagnostic
- P3: Cosmetic/community signaling

## 6) Trigger-to-Action Latency Budgets

- **P0 Safety interlock actions:** ≤ 20 ms end-to-end
- **P1 Operational actuations:** ≤ 100 ms
- **P2 Diagnostic physical indicators:** ≤ 300 ms
- **P3 Cosmetic responses:** ≤ 700 ms

If budget exceeded:
- Raise `LATENCY_BREACH` diagnostic event
- For P0/P1 repeated breaches, degrade to conservative profile or `FAULT_SAFE`

## 7) Subsystem Functional Specs

## 7.1 Sensor Mesh & Telemetry
**Inputs**
- Vibration, thermal, acoustic, proximity, radar/optical, power draw, airflow, actuator position

**Processing**
- Edge filtering, spike rejection, plausibility checks
- Sensor voting for critical detection (2oo3 where feasible)

**Outputs**
- Normalized telemetry stream
- Trigger events with confidence and fault flags

## 7.2 Dynamic Power & Thermal Automation
**Triggers**
- Compute load spike, inverter temperature rise, ambient heat, airflow delta

**Actions**
- Vent louver angle modulation
- Cooling pump speed adjustment
- Heat sink geometry actuation
- Auxiliary power source engagement
- Solar tracking adjustments (if deployed)

**Constraints**
- Never violate L0 actuator inhibits
- Thermal actuation suppressed in `TRAVEL` if external geometry movement is disallowed

## 7.3 Docking & Siding Automation
**Triggers**
- Approach to staging coordinates, optical marker acquisition, rail switch readiness

**Actions**
- Micro-position correction
- Automated switch alignment request/verify
- Grounding lead deployment (stationary only)
- Security barrier deployment after full stop verification

**Accuracy target**
- Sub-centimeter final alignment at designated docking points

## 7.4 Animatronic/Physical Diagnostic Interfaces
**Elements**
- Mechanical gauges
- Kinetic status arms
- Camera/thermal inspection rigs
- Physical hazard markers/flags

**Behavior**
- Mirrors system health classes (green/amber/red + motion pattern)
- Inspection rigs only in `STATIONARY_SERVICE` or `MAINTENANCE`
- Hazard markers auto-deploy on service door open + hazard present

## 7.5 Perimeter & Human Interaction
**Triggers**
- Unauthorized proximity, boundary breach likelihood, after-hours mode

**Responses (non-lethal)**
- Lighting escalation
- Directed acoustic warnings
- Physical barrier repositioning
- Silent remote alert to operator console

**Policy**
- Minimize nuisance alarms
- Community mode uses low-noise visual cues when safe/clear

## 8) Safety, Interlocks, and Manual Override

## 8.1 Hard Interlocks (mandatory)
- If `TRAVEL` active → inhibit all external kinetic/animatronic motion
- If brake/traction ambiguity detected → default inhibit
- If E-stop active → immediate actuator de-energize (except required safety holds)

## 8.2 Manual Override
- Physical quick-release/decouple pin per actuator
- Local lockout/tagout sensing input
- Manual override action logs event + requires reset checklist before re-enable

## 8.3 Default Safe Geometry
- Loss of power/comms causes spring/gravity return-home
- Home position sensors required for verification on restart
- Restart blocked if home verification fails for critical elements

## 9) Fault Handling & Degraded Modes

**Fault classes**
- F1 Minor: continue with monitoring
- F2 Major: disable affected subsystem, continue core operations
- F3 Critical: transition to `FAULT_SAFE`

**Examples**
- Sensor disagreement beyond threshold → degrade affected automation
- Actuator stuck/not-at-command → isolate actuator, publish maintenance fault
- Bus partition detected:
  - Safety bus healthy + telemetry bus failed: operate in reduced observability mode
  - Safety bus fault: immediate `FAULT_SAFE`

## 10) Cybersecurity & Zoning

- Safety zone (L0) physically/logically segmented
- One-way data diode or broker mediation from L0 → L1 where possible
- Mutual auth between edge nodes, rotating credentials
- Signed firmware + secure boot on PLC/MCU/edge controllers
- Local allowlist for command topics and actuator command schemas

## 11) Verification & Validation Plan

## 11.1 Test Methods
- SIL/HIL benches for each actuator family
- Fault injection:
  - sensor drift/spike/dropout
  - stuck actuator
  - delayed/lost messages
  - time sync skew
  - brownout/power loss
- Scenario replay from recorded telemetry

## 11.2 Acceptance Criteria (sample)
- P0 actuation always ≤ 20 ms under nominal and ≤ 30 ms stressed
- 100% safe return-home on forced power cut tests
- Zero unauthorized external motion in `TRAVEL`
- Docking alignment error within spec over N repeated trials

## 12) Minimal Event Schema (Example)

```json
{
  "event_id": "uuid",
  "event_type": "PROXIMITY_ALERT",
  "priority": "P1",
  "source_id": "sensor.prox.07",
  "event_time": "2026-07-30T12:00:00.123Z",
  "state_context": "APPROACH",
  "confidence": 0.94,
  "ttl_ms": 500,
  "safety_impact": "HIGH",
  "payload": {
    "distance_m": 1.8,
    "approach_rate_mps": 0.6,
    "zone": "east_perimeter"
  }
}
```

## 13) Command Gating Truth Matrix (Core)

- **External kinetic deploy allowed?**
  - `TRAVEL`: No
  - `APPROACH`: Limited (only if internal-only movement; no external protrusion)
  - `DOCKING`: Conditional (only docking-certified actuators)
  - `STATIONARY_SERVICE`: Yes (policy-gated)
  - `MAINTENANCE`: Yes (manual supervision)
  - `FAULT_SAFE`: No (except fail-safe return motions)

- **Inspection arm movement allowed?**
  - Only `STATIONARY_SERVICE` / `MAINTENANCE` + L0 permit + door/zone safe

- **Barrier deployment allowed?**
  - `DOCKING`/`STATIONARY_SERVICE` when stop confirmed and path clear

## 14) Implementation Roadmap (90-day)

1. **Weeks 1–3:** Safety predicates, state machine, interlock I/O map  
2. **Weeks 4–6:** Event bus, schema, latency instrumentation  
3. **Weeks 7–9:** Thermal/power automation + docking sequence MVP  
4. **Weeks 10–12:** Animatronic indicators + perimeter choreography  
5. **Weeks 13+:** Fault-injection campaign, certification evidence pack
