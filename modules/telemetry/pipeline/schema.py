"""
Telemetry schema definitions for the Exoskeleton biometric pipeline.

Raw biometric detail is captured here at ingestion time but is only used
locally. Downstream LLM-facing context receives a TelemetryStateSummary
(coarse labels / compact summaries) — never the raw BodyMatrixPayload.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Raw ingestion models (stay local / time-series storage only)
# ---------------------------------------------------------------------------

class HeartRateData(BaseModel):
    """Raw cardiovascular readings from wearable sensor."""

    bpm: float = Field(..., ge=0, le=250, description="Instantaneous heart rate in beats per minute.")
    hrv_ms: Optional[float] = Field(default=None, ge=0, description="Heart-rate variability in milliseconds.")
    resting_hr: Optional[float] = Field(default=None, ge=0, le=250, description="Resting heart rate baseline.")


class MovementData(BaseModel):
    """Raw activity / motion readings."""

    step_count: int = Field(..., ge=0, description="Cumulative step count for the current period.")
    active_calories: Optional[float] = Field(default=None, ge=0, description="Active energy expenditure in kcal.")
    kinetic_intensity: Literal["sedentary", "light", "active", "intense"] = Field(
        default="sedentary",
        description="Coarse activity label derived from accelerometer data.",
    )


class RecoveryMetrics(BaseModel):
    """Sleep and recovery quality indicators."""

    sleep_score: Optional[int] = Field(default=None, ge=0, le=100, description="Overall sleep quality score (0–100).")
    rem_minutes: Optional[int] = Field(default=None, ge=0, description="REM sleep duration in minutes.")
    deep_minutes: Optional[int] = Field(default=None, ge=0, description="Deep-sleep duration in minutes.")
    spo2_percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Blood oxygen saturation (%).")


class BodyMatrixPayload(BaseModel):
    """
    Full atomic telemetry envelope for one observation window.

    This model holds raw biometric detail and must remain within the local
    processing boundary. Do not forward instances of this class to external
    services or LLM prompts. Use TelemetryStateSummary for that purpose.
    """

    timestamp: datetime = Field(..., description="UTC timestamp of the observation.")
    user_id: str = Field(..., min_length=1, description="Opaque local user identifier.")
    heart_rate: HeartRateData
    movement: MovementData
    recovery: Optional[RecoveryMetrics] = None


# ---------------------------------------------------------------------------
# Privacy-safe derived model (safe for LLM context / external services)
# ---------------------------------------------------------------------------

class TelemetryStateSummary(BaseModel):
    """
    Minimized, derived representation of physical state.

    Only coarse labels and compact summaries are stored here — no raw
    biometric values. This is the only telemetry model that should be
    forwarded to the LLM reasoning pipeline or any external service.
    """

    timestamp: datetime = Field(..., description="UTC timestamp of the originating observation.")
    physical_state: Literal["NOMINAL", "LOW_RECOVERY", "ELEVATED_STRESS"] = Field(
        ...,
        description="Coarse physical-state class derived locally from raw telemetry.",
    )
    activity_level: Literal["sedentary", "light", "active", "intense"] = Field(
        ...,
        description="Coarse activity label; mirrors kinetic_intensity from MovementData.",
    )
    recovery_quality: Literal["good", "moderate", "poor", "unknown"] = Field(
        default="unknown",
        description="Coarse sleep/recovery quality derived from sleep_score.",
    )
