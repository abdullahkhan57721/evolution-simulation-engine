"""Tests for immutable portfolio-dashboard presentation models."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.ecology import PatchyResourcePlacement
from evo_engine.genetics import MAX_INTAKE_RATE, MAX_SPEED
from evo_engine.processes import ResourceGeneration
from evo_engine.ui.models import (
    FLAGSHIP_MAX_INTAKE_SCENARIO,
    SCIENCE_AWARE_HIGH_SPEED,
    SCIENCE_AWARE_LOW_SPEED,
    SCIENCE_AWARE_MAX_SPEED_SCENARIO,
    SCIENCE_AWARE_MAX_SPEED_SEED,
    DashboardRun,
    build_curated_config,
    parse_seed_list,
    run_dashboard_experiment,
    run_dashboard_flagship_max_intake,
    run_dashboard_reference,
    run_dashboard_science_aware_max_speed,
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
        mutation_max_change=3,
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
    assert config.mutation_max_change == 3
    assert config.recombination_probability_ppm == 600_000
    assert config.resource_generation_amount == 9
    assert config.resource_deposits_per_step == 3
    assert config.traits.growth_rate == 2

    with pytest.raises(ValueError, match="must not exceed"):
        build_curated_config(initial_population=5, width=2, height=2)
    with pytest.raises(ValueError, match="mutation_percent"):
        build_curated_config(mutation_percent=101)
    with pytest.raises(ValueError, match="mutation_max_change"):
        build_curated_config(mutation_max_change=-1)


def test_disabled_adaptive_branches_ignore_stale_dependent_values() -> None:
    """Test hidden mutation/recombination values cannot leak into model config."""
    config = build_curated_config(
        mutation_enabled=False,
        mutation_percent=83,
        mutation_max_change=19,
        recombination_enabled=False,
        recombination_percent=77,
    )

    assert config.mutation_probability_ppm == 0
    assert config.mutation_max_change == 0
    assert config.recombination_probability_ppm == 0


def test_adaptive_branch_flags_are_explicit_booleans() -> None:
    """Test branch activation cannot be supplied through truthy non-Booleans."""
    with pytest.raises(TypeError, match="mutation_enabled"):
        build_curated_config(mutation_enabled=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="recombination_enabled"):
        build_curated_config(recombination_enabled=1)  # type: ignore[arg-type]


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
    assert result.individual_trait_history == ()
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
        "individual_trait_history",
        "scenario",
    )
    assert not hasattr(result, "engine")
    assert not hasattr(result, "simulation")
    assert not hasattr(result, "world")
    assert not hasattr(result, "recorder")


def test_dashboard_reference_records_only_requested_individual_traits() -> None:
    """Test focal replay evidence is opt-in committed scalar history only."""
    config = build_curated_config(
        seed=23,
        max_steps=2,
        initial_population=4,
        width=4,
        height=4,
        resource_deposits_per_step=2,
    )

    result = run_dashboard_reference(
        config,
        individual_trait_names=(MAX_SPEED,),
    )

    assert len(result.individual_trait_history) == len(result.spatial_history) == 3
    assert all(
        observation.trait_names == (MAX_SPEED,)
        for observation in result.individual_trait_history
    )
    for spatial, traits in zip(
        result.spatial_history,
        result.individual_trait_history,
        strict=True,
    ):
        assert traits.step_index == spatial.step_index
        assert tuple(item.organism_id for item in traits.individuals) == tuple(
            item.organism_id for item in spatial.organisms
        )
        assert all(
            isinstance(traits.trait_value(item.organism_id, MAX_SPEED), int)
            for item in spatial.organisms
        )

    with pytest.raises(TypeError, match="individual_trait_names"):
        run_dashboard_reference(
            config,
            individual_trait_names=[MAX_SPEED],  # type: ignore[arg-type]
        )


def test_dashboard_reference_runs_with_adaptive_branches_disabled() -> None:
    """Test canonical disabled branches execute through the real reference preset."""
    config = build_curated_config(
        max_steps=1,
        initial_population=4,
        width=4,
        height=4,
        mutation_enabled=False,
        mutation_percent=91,
        mutation_max_change=17,
        recombination_enabled=False,
        recombination_percent=88,
    )

    result = run_dashboard_reference(config)

    assert result.completed_steps == 1
    assert result.config.mutation_probability_ppm == 0
    assert result.config.mutation_max_change == 0
    assert result.config.recombination_probability_ppm == 0


def test_dashboard_flagship_uses_committed_canonical_evidence() -> None:
    """Test the featured dashboard route reuses the canonical flagship run."""
    result = run_dashboard_flagship_max_intake()

    assert result.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO
    assert result.config.seed == 41
    assert result.completed_steps == 40
    assert result.final_population_size > 0
    assert result.genetic_history[0].locus(MAX_INTAKE_RATE).allele_frequency(8) == 0.5
    assert result.genetic_history[30].locus(MAX_INTAKE_RATE).allele_frequency(8) > 0.85
    assert dict(result.event_counts).get("Predation", 0) == 0


def test_dashboard_flagship_can_opt_into_selected_individual_evidence() -> None:
    """Test curated runs can request one committed focal trait without live owners."""
    result = run_dashboard_flagship_max_intake(
        individual_trait_names=(MAX_INTAKE_RATE,),
    )

    assert len(result.individual_trait_history) == len(result.spatial_history)
    assert result.individual_trait_history[0].trait_names == (MAX_INTAKE_RATE,)
    assert result.individual_trait_history[0].trait_value(0, MAX_INTAKE_RATE) in (2, 8)


def test_science_aware_speed_preview_combines_real_b1_b2_evidence() -> None:
    """Test the preview is committed B1/B2 evidence, not renderer reconstruction."""
    result = run_dashboard_science_aware_max_speed()

    assert result.scenario == SCIENCE_AWARE_MAX_SPEED_SCENARIO
    assert result.config.seed == SCIENCE_AWARE_MAX_SPEED_SEED
    assert result.config.mutation_probability_ppm == 0
    assert isinstance(result.config.resource_placement_model, PatchyResourcePlacement)
    assert result.completed_steps == 30
    assert len(result.individual_trait_history) == len(result.spatial_history) == 31
    founder_traits = result.individual_trait_history[0]
    assert founder_traits.trait_names == (MAX_SPEED,)
    assert {
        founder_traits.trait_value(item.organism_id, MAX_SPEED)
        for item in founder_traits.individuals
    } == {SCIENCE_AWARE_LOW_SPEED, SCIENCE_AWARE_HIGH_SPEED}

    for frame, traits in zip(
        result.spatial_history,
        result.individual_trait_history,
        strict=True,
    ):
        assert frame.step_index == traits.step_index
        assert tuple(item.organism_id for item in frame.organisms) == tuple(
            item.organism_id for item in traits.individuals
        )

    patches = result.config.resource_placement_model.patches
    generation_events = tuple(
        applied.event
        for step in result.telemetry_steps
        for applied in step.events_for_process("ResourceGeneration")
    )
    assert generation_events
    assert all(
        isinstance(event, ResourceGeneration.Event) for event in generation_events
    )
    assert all(
        any(
            (event.x - patch.center_x) ** 2 + (event.y - patch.center_y) ** 2
            <= patch.radius**2
            for patch in patches
        )
        for event in generation_events
        if isinstance(event, ResourceGeneration.Event)
    )


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


def test_dashboard_flagship_experiment_reuses_flagship_runner() -> None:
    """Test the featured experiment path does not reconstruct custom orchestration."""
    config = build_curated_config(max_steps=1)

    result = run_dashboard_experiment(
        config,
        seeds=(41,),
        scenario=FLAGSHIP_MAX_INTAKE_SCENARIO,
    )

    replicate = result.replicates[0]
    assert result.seeds == (41,)
    assert replicate.metadata.completed_steps == 40
    assert (
        replicate.genetic_history[0].locus(MAX_INTAKE_RATE).allele_frequency(8) == 0.5
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
