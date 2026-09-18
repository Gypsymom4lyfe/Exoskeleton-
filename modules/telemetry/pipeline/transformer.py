"""
Telemetry transformer: converts raw BodyMatrixPayload into a
privacy-safe TelemetryStateSummary.

Design note (Privacy-Safe):
  Raw high-frequency biometric data (BodyMatrixPayload) never leaves this
  module.  Only the derived TelemetryStateSummary — containing coarse state
  labels and no raw metric values — is returned for downstream use.
"""

from __future__ import annotations

from modules.telemetry.pipeline.schema import (
    BodyMatrixPayload,
    TelemetryStateSummary,
)


def _derive_recovery_quality(sleep_score: int | None) -> str:
    """Map a numeric sleep score to a coarse quality label."""
    if sleep_score is None:
        return "unknown"
    if sleep_score >= 80:
        return "good"
    if sleep_score >= 60:
        return "moderate"
    return "poor"


def summarize(payload: BodyMatrixPayload) -> TelemetryStateSummary:
    """
    Convert a raw BodyMatrixPayload into a TelemetryStateSummary.

    All classification logic runs locally. The returned summary contains only
    coarse state labels; no raw numeric biometric values are propagated.

    Args:
        payload: A raw telemetry envelope (must stay within local boundary).

    Returns:
        A TelemetryStateSummary safe to pass to the LLM context layer.
    """
    hr = payload.heart_rate.bpm
    hrv = payload.heart_rate.hrv_ms
    sleep_score = payload.recovery.sleep_score if payload.recovery is not None else None

    # Determine coarse physical state using explicit None checks to avoid
    # false-negative truthiness on legitimate zero / low values.
    if hr > 100 and hrv is not None and hrv < 30:
        physical_state = "ELEVATED_STRESS"
    elif sleep_score is not None and sleep_score < 60:
        physical_state = "LOW_RECOVERY"
    else:
        physical_state = "NOMINAL"

    return TelemetryStateSummary(
        timestamp=payload.timestamp,
        physical_state=physical_state,
        activity_level=payload.movement.kinetic_intensity,
        recovery_quality=_derive_recovery_quality(sleep_score),
    )
