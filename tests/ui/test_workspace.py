"""Focused tests for completed-result workspace presentation helpers."""

from evo_engine.ui.workspace import _next_step, _previous_step, _summary_mean


def test_summary_mean_handles_empty_authoritative_population() -> None:
    """Test an absent authoritative mean renders without formatting errors."""
    assert _summary_mean(None) == "—"
    assert _summary_mean(3.25) == "3.2"


def test_previous_and_next_step_follow_recorded_committed_order() -> None:
    """Test playback navigation uses recorded step order rather than assumptions."""
    steps = (0, 2, 5)

    assert _previous_step(steps, 0) == 0
    assert _previous_step(steps, 5) == 2
    assert _next_step(steps, 0) == 2
    assert _next_step(steps, 5) == 5
