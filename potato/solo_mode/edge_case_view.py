"""Presentation states for the Solo Mode edge-case workflow."""

from dataclasses import dataclass
from typing import ClassVar, List, Optional, Union

from .edge_case_synthesizer import EdgeCase, SynthesisError
from .phase_controller import SoloPhase


@dataclass(frozen=True)
class LabelingEdgeCase:
    kind: ClassVar[str] = "labeling"
    current_case: EdgeCase
    remaining_count: int


@dataclass(frozen=True)
class SynthesisBlocked:
    kind: ClassVar[str] = "blocked"
    error: SynthesisError
    remaining_count: int = 0


@dataclass(frozen=True)
class EdgeCasesComplete:
    kind: ClassVar[str] = "complete"
    remaining_count: int = 0


EdgeCasePageState = Union[
    LabelingEdgeCase,
    SynthesisBlocked,
    EdgeCasesComplete,
]


def build_edge_case_page_state(
    unlabeled_cases: List[EdgeCase],
    phase: SoloPhase,
    synthesis_error: Optional[SynthesisError] = None,
) -> EdgeCasePageState:
    """Build exactly one page state from the current workflow data."""
    if synthesis_error is not None:
        return SynthesisBlocked(synthesis_error)
    if unlabeled_cases:
        return LabelingEdgeCase(unlabeled_cases[0], len(unlabeled_cases))
    if phase in (SoloPhase.EDGE_CASE_SYNTHESIS, SoloPhase.EDGE_CASE_LABELING):
        return SynthesisBlocked(SynthesisError(
            "No edge cases are available. Retry synthesis to continue."
        ))
    return EdgeCasesComplete()
