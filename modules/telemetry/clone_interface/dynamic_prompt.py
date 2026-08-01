from modules.telemetry.pipeline.schema import BodyMatrixPayload


def generate_telemetry_header(telemetry: BodyMatrixPayload) -> str:
    """Generate a privacy-safe context block using only minimized, derived telemetry."""

    hr = telemetry.heart_rate.bpm
    hrv = telemetry.heart_rate.hrv_ms
    sleep_score = telemetry.recovery.sleep_score if telemetry.recovery else None
    step_count = telemetry.movement.step_count

    if hr > 100 and hrv is not None and hrv < 30:
        physical_state = "ELEVATED_STRESS"
        tone_instruction = "Use a direct, concise, grounded tone."
    elif sleep_score is not None and sleep_score < 60:
        physical_state = "LOW_RECOVERY"
        tone_instruction = "Use a calm, supportive, energy-efficient tone."
    else:
        physical_state = "NOMINAL"
        tone_instruction = "Use standard interactive tone."

    return f"""<BIOLOGICAL_TELEMETRY_CONTEXT>
Signal Summary: derived local telemetry only
Timestamp: {telemetry.timestamp.isoformat()}
State Class: {physical_state}
Activity Level: {step_count}
Directive: {tone_instruction}
</BIOLOGICAL_TELEMETRY_CONTEXT>"""
