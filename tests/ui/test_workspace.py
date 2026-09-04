"""Focused tests for completed-result workspace presentation helpers."""

from evo_engine.genetics import MAX_SPEED
from evo_engine.presets.reference_ecology.config import (
    REFERENCE_TRAIT_DOMAINS,
    ReferenceEcologyConfig,
)
from evo_engine.ui.models import (
    REFERENCE_SCENARIO,
    SCIENCE_AWARE_MAX_SPEED_SCENARIO,
    DashboardRun,
)
from evo_engine.ui.workspace import (
    _focal_encoding_for_run,
    _next_step,
    _preferred_science_variable,
    _previous_step,
    _summary_mean,
)


def _empty_run(*, scenario: str) -> DashboardRun:
    return DashboardRun(
        config=ReferenceEcologyConfig(),
        completed_steps=0,
        population_history=(),
        genetic_history=(),
        spatial_history=(),
        telemetry_steps=(),
        life_histories=(),
        scenario=scenario,
    )


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


def test_science_aware_preview_uses_fixed_shared_max_speed_encoding() -> None:
    """Test only the recognized preview activates fixed scientific world meaning."""
    preview = _empty_run(scenario=SCIENCE_AWARE_MAX_SPEED_SCENARIO)
    encoding = _focal_encoding_for_run(preview)

    assert encoding is not None
    assert encoding.trait_name == MAX_SPEED
    assert encoding.label == "Maximum speed"
    assert (encoding.lower_bound, encoding.upper_bound) == REFERENCE_TRAIT_DOMAINS[
        MAX_SPEED
    ]
    assert _preferred_science_variable(preview) == MAX_SPEED

    generic = _empty_run(scenario=REFERENCE_SCENARIO)
    assert _focal_encoding_for_run(generic) is None
    assert _preferred_science_variable(generic) == "growth_rate"
