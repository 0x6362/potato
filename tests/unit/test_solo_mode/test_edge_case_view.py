from potato.solo_mode.edge_case_synthesizer import EdgeCase, SynthesisError
from potato.solo_mode.edge_case_view import (
    EdgeCasesComplete,
    LabelingEdgeCase,
    SynthesisBlocked,
    build_edge_case_page_state,
)
from potato.solo_mode.phase_controller import SoloPhase


def _edge_case(case_id="edge_0001"):
    return EdgeCase(
        id=case_id,
        text="Mixed sentiment",
        boundary_labels=["positive", "negative"],
        difficulty_reason="Contains both signals",
        which_aspect="mixed valence",
    )


def test_labels_the_first_available_edge_case():
    page = build_edge_case_page_state(
        [_edge_case("edge_0001"), _edge_case("edge_0002")],
        SoloPhase.EDGE_CASE_LABELING,
    )

    assert isinstance(page, LabelingEdgeCase)
    assert page.current_case.id == "edge_0001"
    assert page.remaining_count == 2


def test_models_synthesis_failure_as_retryable_page_state():
    error = SynthesisError("provider rejected request")

    page = build_edge_case_page_state(
        [],
        SoloPhase.EDGE_CASE_SYNTHESIS,
        synthesis_error=error,
    )

    assert isinstance(page, SynthesisBlocked)
    assert page.error == error


def test_repairs_legacy_empty_labeling_state_with_retry_option():
    page = build_edge_case_page_state([], SoloPhase.EDGE_CASE_LABELING)

    assert isinstance(page, SynthesisBlocked)
    assert page.error.retryable is True


def test_no_cases_after_edge_case_workflow_is_complete():
    page = build_edge_case_page_state([], SoloPhase.PROMPT_VALIDATION)

    assert isinstance(page, EdgeCasesComplete)
