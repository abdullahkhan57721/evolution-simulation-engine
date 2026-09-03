"""Tests for immutable portfolio-dashboard presentation models."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.ui.models import (
    DashboardRun,
    build_curated_config,
    parse_seed_list,
    run_dashboard_experiment,
    run_dashboard_reference,
)


def test_build_curated_config_reuses_reference_validation_contracts() -> None:
    """Test curated controls map into the existing reference configuration."""
    config = build_curated_config(
        seed=7,
        max_steps=3,
        initial_population=4,
        width=5,
        height=4,
        initial_energy=25,
        mutation_percent=2,
        recombination_percent=60,
        resource_generation_amount=9,
        resource_deposits_per_step=3,
        growth_rate=2,
    )

    assert config.seed == 7
    assert config.max_steps == 3
    assert config.initial_population == 4
    assert config.width == 5
    assert config.height == 4
    assert config.initial_energy == 25
    assert config.mutation_probability_ppm == 20_000
    assert config.recombination_probability_ppm == 600_000
    assert config.resource_generation_amount == 9
    assert config.resource_deposits_per_step == 3
    assert config.traits.growth_rate == 2

    with pytest.raises(ValueError, match="must not exceed"):
        build_curated_config(initial_population=5, width=2, height=2)
    with pytest.raises(ValueError, match="mutation_percent"):
        build_curated_config(mutation_percent=101)


def test_dashboard_run_contains_only_immutable_completed_result_values() -> None:
    """Test the session-facing result excludes live engine/world ownership."""
    config = build_curated_config(
        seed=19,
        max_steps=2,
        initial_population=4,
        width=4,
        height=4,
        resource_deposits_per_step=2,
    )

    result = run_dashboard_reference(config)

    assert isinstance(result, DashboardRun)
    assert result.completed_steps == 2
    assert result.population_history[-1].step_index == 2
    assert result.spatial_history[-1].step_index == 2
    assert result.genetic_history[-1].step_index == 2
    assert len(result.population_history) == len(result.spatial_history) == 3
    assert result.final_population_size == result.population_history[-1].population_size
    assert result.final_total_resources == result.population_history[-1].total_resources
    assert result.total_births == sum(
        not history.is_founder for history in result.life_histories
    )
    assert result.total_deaths == sum(
        not history.is_alive for history in result.life_histories
    )
    assert tuple(field.name for field in attrs.fields(DashboardRun)) == (
        "config",
        "completed_steps",
        "population_history",
        "genetic_history",
        "spatial_history",
        "telemetry_steps",
        "life_histories",
    )
    assert not hasattr(result, "engine")
    assert not hasattr(result, "simulation")
    assert not hasattr(result, "world")
    assert not hasattr(result, "recorder")


def test_dashboard_experiment_delegates_to_existing_replicate_contract() -> None:
    """Test small UI experiments return the canonical experiment result."""
    config = build_curated_config(
        max_steps=1,
        initial_population=4,
        width=4,
        height=4,
    )

    result = run_dashboard_experiment(config, seeds=(3, 5))

    assert result.seeds == (3, 5)
    assert all(
        replicate.metadata.completed_steps == 1 for replicate in result.replicates
    )
    assert all(
        len(replicate.population_history) == 2 for replicate in result.replicates
    )


def test_parse_seed_list_is_bounded_unique_and_understandable() -> None:
    """Test interactive experiment seed parsing rejects expensive/bad input."""
    assert parse_seed_list(" 1, 2,3 ") == (1, 2, 3)

    with pytest.raises(ValueError, match="at least one"):
        parse_seed_list(" , ")
    with pytest.raises(ValueError, match="comma-separated integers"):
        parse_seed_list("1, nope")
    with pytest.raises(ValueError, match="unique"):
        parse_seed_list("1, 1")
    with pytest.raises(ValueError, match="at most 8"):
        parse_seed_list("1,2,3,4,5,6,7,8,9")
