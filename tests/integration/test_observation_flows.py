"""Integration tests for evolutionary observation flows."""

from __future__ import annotations

from evo_engine.genetics import GROWTH_RATE, METABOLIC_COST_COEFFICIENT
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def test_reference_ecology_records_baseline_and_each_completed_step() -> None:
    """Test the complete reference preset produces an evolutionary time series."""
    config = ReferenceEcologyConfig(
        initial_population=4,
        max_steps=3,
        seed=17,
    )
    ecology = build_reference_ecology(config)

    ecology.engine.run(ecology.simulation)

    observations = ecology.recorder.observations
    assert tuple(observation.step_index for observation in observations) == (
        0,
        1,
        2,
        3,
    )
    assert observations[0].population_size == config.initial_population
    assert len(observations[0].traits) == len(config.traits.as_mapping())

    founder_growth_rate = observations[0].trait(GROWTH_RATE)
    assert founder_growth_rate.value_counts == ((config.traits.growth_rate, 4),)
    assert founder_growth_rate.summary.mean == float(config.traits.growth_rate)

    founder_metabolic_coefficient = observations[0].trait(METABOLIC_COST_COEFFICIENT)
    assert founder_metabolic_coefficient.value_counts == (
        (config.traits.metabolic_cost_coefficient, 4),
    )


def test_reference_ecology_records_causal_events_for_each_committed_step() -> None:
    """Test reference runs expose process-level causes alongside state history."""
    config = ReferenceEcologyConfig(
        initial_population=4,
        max_steps=3,
        seed=17,
    )
    ecology = build_reference_ecology(config)

    ecology.engine.run(ecology.simulation)

    steps = ecology.event_recorder.steps
    assert tuple(step.completed_step_index for step in steps) == (1, 2, 3)
    assert all(step.events for step in steps)
    assert ecology.event_recorder.events_for_process("ResourceGeneration")
    assert all(event.stage_index >= 0 for event in ecology.event_recorder.events)


def test_reference_observations_are_historical_values_not_live_world_views() -> None:
    """Test later simulation mutation cannot rewrite an earlier observation."""
    config = ReferenceEcologyConfig(
        initial_population=2,
        max_steps=1,
        seed=19,
    )
    ecology = build_reference_ecology(config)
    ecology.engine.run(ecology.simulation)

    baseline = ecology.recorder.observations[0]
    baseline_energy = baseline.energy
    first_organism = next(iter(ecology.simulation.state.world.organisms.values()))
    first_organism.change_energy(100)

    assert ecology.recorder.observations[0].energy == baseline_energy
