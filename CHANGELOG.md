# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Physiological telemetry simulator at `simulators/physiology_telemetry_generator.py`
- Dependency declaration in `requirements.txt` (`requests`)
- Validation and run instructions in `READ.md`
- Standardized project documentation set:
  - `README.md`
  - `docs/architecture.md`
  - `docs/runbook.md`
  - `docs/ideas.md`
  - `CHANGELOG.md`

### Notes
- Simulator posts telemetry every 2 seconds to a configurable `GATEWAY_URL`.
