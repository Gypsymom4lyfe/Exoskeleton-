from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class HeartRateData(BaseModel):
    bpm: float = Field(..., ge=0, le=250)
    hrv_ms: Optional[float] = Field(default=None, ge=0)
    resting_hr: Optional[float] = Field(default=None, ge=0, le=250)


class MovementData(BaseModel):
    step_count: int = Field(..., ge=0)
    active_calories: Optional[float] = Field(default=None, ge=0)
    kinetic_intensity: Literal["sedentary", "light", "active", "intense"] = "sedentary"


class RecoveryMetrics(BaseModel):
    sleep_score: Optional[int] = Field(default=None, ge=0, le=100)
    rem_minutes: Optional[int] = Field(default=None, ge=0)
    deep_minutes: Optional[int] = Field(default=None, ge=0)
    spo2_percentage: Optional[float] = Field(default=None, ge=0, le=100)


class BodyMatrixPayload(BaseModel):
    timestamp: datetime
    user_id: str = Field(..., min_length=1)
    heart_rate: HeartRateData
    movement: MovementData
    recovery: Optional[RecoveryMetrics] = None
