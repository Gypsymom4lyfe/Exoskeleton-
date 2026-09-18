"""
State evaluator: translates a TelemetryStateSummary into behavioral directives
for the LLM context layer.

This module operates exclusively on derived/minimized data (TelemetryStateSummary)
and never touches raw biometric values.  It produces a StateEvaluation — a
pair of (label, tone directive) — that is safe to embed in LLM system prompts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from modules.telemetry.pipeline.schema import TelemetryStateSummary


PhysicalState = Literal["NOMINAL", "LOW_RECOVERY", "ELEVATED_STRESS"]


@dataclass(frozen=True)
class StateEvaluation:
    """
    Output of the state evaluator: a coarse label and a prose directive.

    Both fields contain only generic, non-identifying language that is safe
    to include in an LLM system prompt without exposing raw health detail.
    """

    physical_state: PhysicalState
    tone_directive: str


# Directive lookup — centralised so changes apply consistently.
_DIRECTIVES: dict[str, str] = {
    "ELEVATED_STRESS": (
        "Use a direct, concise, and grounded tone. "
        "Avoid dense walls of text. Prioritize clarity and brevity."
    ),
    "LOW_RECOVERY": (
        "Use a calm, highly supportive, and energy-efficient tone. "
        "Keep responses short and easy to absorb."
    ),
    "NOMINAL": "Use standard interactive tone.",
}


def evaluate(summary: TelemetryStateSummary) -> StateEvaluation:
    """
    Derive a StateEvaluation from a privacy-safe TelemetryStateSummary.

    Args:
        summary: Derived state summary produced by transformer.summarize().

    Returns:
        A StateEvaluation containing a coarse label and tone directive.
    """
    directive = _DIRECTIVES.get(summary.physical_state, _DIRECTIVES["NOMINAL"])
    return StateEvaluation(
        physical_state=summary.physical_state,
        tone_directive=directive,
    )
