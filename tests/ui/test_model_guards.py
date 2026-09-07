"""Focused validation coverage for retained dashboard presentation models."""

from __future__ import annotations

import pytest

from evo_engine.ui.models import (
    DashboardRun,
    build_curated_config,
    parse_seed_list,
    run_dashboard_experiment,
    run_dashboard_reference,
)


def test_empty_dashboard_run_has_zero_final_summary_values() -> None:
    run = DashboardRun(
        config=build_curated_config(),
        completed_steps=0,
        population_history=(),
        genetic_history=(),
        spatial_history=(),
        telemetry_steps=(),
        life_histories=(),
    )

    assert run.final_population_size == 0
    assert run.final_total_resources == 0
    assert run.final_carcass_count == 0
    assert run.total_births == 0
    assert run.total_deaths == 0
    assert run.event_counts == ()


def test_curated_config_rejects_invalid_retained_adaptive_values() -> None:
    with pytest.raises(ValueError, match="recombination_percent"):
        build_curated_config(recombination_percent=101)
    with pytest.raises(ValueError, match="gaussian_standard_deviation"):
        build_curated_config(
            exploration_movement_kind="gaussian",
            gaussian_standard_deviation=-1,
        )
    with pytest.raises(ValueError, match="exploration_movement_kind"):
        build_curated_config(exploration_movement_kind="unsupported")


def test_dashboard_runners_reject_non_reference_configuration() -> None:
    with pytest.raises(TypeError, match="ReferenceEcologyConfig"):
        run_dashboard_reference(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ReferenceEcologyConfig"):
        run_dashboard_experiment(object(), seeds=(1,))  # type: ignore[arg-type]


def test_dashboard_experiment_rejects_unknown_scenario() -> None:
    config = build_curated_config(max_steps=1, initial_population=1, width=2, height=2)

    with pytest.raises(ValueError, match="Unsupported dashboard scenario"):
        run_dashboard_experiment(config, seeds=(1,), scenario="unknown")


def test_seed_parser_requires_string_input() -> None:
    with pytest.raises(TypeError, match="seed list"):
        parse_seed_list(1)  # type: ignore[arg-type]
