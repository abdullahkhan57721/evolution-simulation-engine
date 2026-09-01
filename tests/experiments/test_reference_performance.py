"""Tests for deterministic reference-ecology performance measurement."""

from __future__ import annotations

from pathlib import Path

import pytest

from evo_engine.experiments.performance import (
    ReferencePerformanceScenario,
    benchmark_reference_scenario,
    profile_reference_scenario,
)
from evo_engine.presets import ReferenceEcologyConfig


def _tiny_scenario(*, observed: bool = False) -> ReferencePerformanceScenario:
    return ReferencePerformanceScenario(
        name="tiny-observed" if observed else "tiny-core",
        config=ReferenceEcologyConfig(
            width=2,
            height=1,
            initial_population=2,
            max_steps=1,
            seed=7,
        ),
        observed=observed,
    )


def test_benchmark_records_repeated_runtime_and_stable_outcome() -> None:
    """Test timing repeats use fresh state and preserve deterministic outcomes."""
    result = benchmark_reference_scenario(
        _tiny_scenario(),
        repeats=2,
        warmups=1,
    )

    assert result.scenario_name == "tiny-core"
    assert result.observed is False
    assert result.repeats == 2
    assert result.warmups == 1
    assert len(result.durations_seconds) == 2
    assert all(duration >= 0.0 for duration in result.durations_seconds)
    assert result.minimum_seconds <= result.median_seconds <= result.maximum_seconds
    assert result.minimum_seconds <= result.mean_seconds <= result.maximum_seconds
    assert result.outcome.completed_steps == 1
    assert result.median_seconds_per_step == result.median_seconds


def test_benchmark_supports_full_observation_stack() -> None:
    """Test observed performance scenarios execute the reference recorder stack."""
    result = benchmark_reference_scenario(
        _tiny_scenario(observed=True),
        repeats=1,
        warmups=0,
    )

    assert result.scenario_name == "tiny-observed"
    assert result.observed is True
    assert result.outcome.completed_steps == 1


def test_profile_reports_cumulative_runtime_and_can_dump_raw_stats(
    tmp_path: Path,
) -> None:
    """Test cProfile output is inspectable as text and reusable raw stats."""
    stats_path = tmp_path / "tiny.prof"

    result = profile_reference_scenario(
        _tiny_scenario(),
        top_functions=10,
        stats_path=str(stats_path),
    )

    assert result.scenario_name == "tiny-core"
    assert result.observed is False
    assert result.total_calls > 0
    assert result.primitive_calls > 0
    assert result.total_seconds >= 0.0
    assert "function calls" in result.report
    assert "cumulative" in result.report
    assert result.outcome.completed_steps == 1
    assert stats_path.is_file()
    assert stats_path.stat().st_size > 0


@pytest.mark.parametrize(
    ("repeats", "warmups", "message"),
    [
        (0, 0, "repeats"),
        (1, -1, "warmups"),
    ],
)
def test_benchmark_rejects_invalid_measurement_counts(
    repeats: int,
    warmups: int,
    message: str,
) -> None:
    """Test measurement counts reject empty repeats and negative warmups."""
    with pytest.raises(ValueError, match=message):
        benchmark_reference_scenario(
            _tiny_scenario(),
            repeats=repeats,
            warmups=warmups,
        )


def test_scenario_rejects_blank_name() -> None:
    """Test performance scenarios require stable nonblank names."""
    with pytest.raises(ValueError, match="name"):
        ReferencePerformanceScenario(
            name=" ",
            config=ReferenceEcologyConfig(),
        )


def test_profile_rejects_blank_stats_path() -> None:
    """Test raw profile destinations cannot be empty."""
    with pytest.raises(ValueError, match="stats_path"):
        profile_reference_scenario(
            _tiny_scenario(),
            stats_path=" ",
        )
