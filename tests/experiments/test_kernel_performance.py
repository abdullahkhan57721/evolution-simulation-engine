"""Tests for domain-neutral simulation-kernel performance measurement."""

from __future__ import annotations

from pathlib import Path

from evo_engine.experiments.kernel_performance import (
    KernelPerformanceScenario,
    benchmark_kernel_scenario,
    profile_kernel_scenario,
)


def _tiny_scenario(*, journaled: bool = False) -> KernelPerformanceScenario:
    return KernelPerformanceScenario(
        name="tiny-journaled" if journaled else "tiny-core",
        steps=2,
        events_per_step=3,
        journaled=journaled,
    )


def test_benchmark_is_domain_neutral_and_deterministic() -> None:
    """Test synthetic kernel timing preserves a fixed trivial outcome."""
    result = benchmark_kernel_scenario(
        _tiny_scenario(),
        repeats=2,
        warmups=1,
    )

    assert result.scenario_name == "tiny-core"
    assert result.journaled is False
    assert result.repeats == 2
    assert result.warmups == 1
    assert len(result.durations_seconds) == 2
    assert all(duration >= 0.0 for duration in result.durations_seconds)
    assert result.outcome.completed_steps == 2
    assert result.outcome.applied_events == 6
    assert result.outcome.final_step_event_count == 3
    assert result.median_seconds_per_event == result.median_seconds / 6


def test_benchmark_exercises_generic_effect_journaling() -> None:
    """Test the journaled baseline preserves the same deterministic outcome."""
    result = benchmark_kernel_scenario(
        _tiny_scenario(journaled=True),
        repeats=1,
        warmups=0,
    )

    assert result.scenario_name == "tiny-journaled"
    assert result.journaled is True
    assert result.outcome.completed_steps == 2
    assert result.outcome.applied_events == 6
    assert result.outcome.final_step_event_count == 3


def test_profile_reports_kernel_runtime_and_dumps_raw_stats(tmp_path: Path) -> None:
    """Test kernel profiles remain inspectable as text and raw pstats."""
    stats_path = tmp_path / "kernel.prof"

    result = profile_kernel_scenario(
        _tiny_scenario(),
        top_functions=20,
        stats_path=str(stats_path),
    )

    assert result.scenario_name == "tiny-core"
    assert result.journaled is False
    assert "function calls" in result.report
    assert "stage_coordinator.py" in result.report
    assert result.outcome.applied_events == 6
    assert stats_path.is_file()
    assert stats_path.stat().st_size > 0
