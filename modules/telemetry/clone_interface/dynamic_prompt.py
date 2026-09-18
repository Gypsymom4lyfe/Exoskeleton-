"""
Dynamic prompt composer: formats minimized telemetry state into a
privacy-safe LLM system-context block.

Privacy design:
  - Input: TelemetryStateSummary — coarse labels only, no raw biometrics.
  - Output: A compact XML-tagged prompt block containing only state labels
    and behavioral directives.
  - Raw biometric values (HR, HRV, sleep score, SpO2, etc.) are never
    included in the prompt.
  - Explicit `is not None` checks are used throughout to avoid brittle
    truthiness failures on legitimate zero or low numeric values.
"""

from __future__ import annotations

from modules.telemetry.pipeline.schema import TelemetryStateSummary
from modules.telemetry.clone_interface.state_evaluator import evaluate


def generate_telemetry_header(summary: TelemetryStateSummary) -> str:
    """
    Generate a privacy-safe context block for the LLM system prompt.

    Only coarse, derived state labels are embedded — no raw biometric values.
    The block is intentionally compact to minimise token consumption and
    reduce the risk of sensitive data leaking into model context.

    Args:
        summary: A TelemetryStateSummary produced by transformer.summarize().
                 Must not contain raw BodyMatrixPayload data.

    Returns:
        A formatted string safe for inclusion in an LLM system prompt.
    """
    evaluation = evaluate(summary)

    return (
        "<PHYSICAL_STATE_CONTEXT>\n"
        f"Signal source: derived local telemetry (privacy-minimized)\n"
        f"Timestamp: {summary.timestamp.isoformat()}\n"
        f"State class: {evaluation.physical_state}\n"
        f"Activity level: {summary.activity_level}\n"
        f"Recovery quality: {summary.recovery_quality}\n"
        f"Directive: {evaluation.tone_directive}\n"
        "</PHYSICAL_STATE_CONTEXT>"
    )
