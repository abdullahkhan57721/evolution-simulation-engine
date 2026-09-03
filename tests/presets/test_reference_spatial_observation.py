"""Integration tests for reference-ecology spatial observation."""

from __future__ import annotations

from evo_engine.observation import SpatialRecorder
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def test_reference_ecology_adds_spatial_observer_only_when_requested() -> None:
    """Test spatial recording is additive rather than a default preset cost."""
    config = ReferenceEcologyConfig(
        width=5,
        height=4,
        initial_population=4,
        max_steps=2,
        seed=73,
    )
    spatial_recorder = SpatialRecorder()

    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial_recorder,),
    )
    default_ecology = build_reference_ecology(config)

    assert ecology.recorder in ecology.engine.observers
    assert ecology.genetic_recorder in ecology.engine.observers
    assert ecology.pedigree_recorder in ecology.engine.observers
    assert spatial_recorder in ecology.engine.observers
    assert ecology.event_recorder in ecology.engine.telemetry_observers
    assert not any(
        isinstance(observer, SpatialRecorder)
        for observer in default_ecology.engine.observers
    )


def test_reference_spatial_history_aligns_with_committed_population_history() -> None:
    """Test every reference spatial frame agrees with committed summary records."""
    config = ReferenceEcologyConfig(
        width=5,
        height=4,
        initial_population=4,
        max_steps=3,
        seed=73,
    )
    spatial_recorder = SpatialRecorder()
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial_recorder,),
    )

    ecology.engine.run(ecology.simulation)
    first_history = spatial_recorder.observations
    ecology.engine.run(ecology.simulation)

    assert spatial_recorder.observations == first_history
    assert len(spatial_recorder.observations) == config.max_steps + 1
    assert tuple(frame.step_index for frame in spatial_recorder.observations) == tuple(
        observation.step_index for observation in ecology.recorder.observations
    )

    for frame, population in zip(
        spatial_recorder.observations,
        ecology.recorder.observations,
        strict=True,
    ):
        assert len(frame.organisms) == population.population_size
        assert sum(resource.amount for resource in frame.resources) == (
            population.total_resources
        )
        assert len(frame.carcasses) == population.carcass_count
        assert all(0 <= organism.x < frame.world_width for organism in frame.organisms)
        assert all(0 <= organism.y < frame.world_height for organism in frame.organisms)
        assert all(0 <= resource.x < frame.world_width for resource in frame.resources)
        assert all(0 <= resource.y < frame.world_height for resource in frame.resources)
        assert all(0 <= carcass.x < frame.world_width for carcass in frame.carcasses)
        assert all(0 <= carcass.y < frame.world_height for carcass in frame.carcasses)

    final_world = ecology.simulation.state.domain_state
    final_frame = spatial_recorder.observations[-1]
    assert final_frame.organisms == tuple(
        type(final_frame.organisms[0])(
            organism_id=organism_id,
            x=organism.x,
            y=organism.y,
            age=organism.age,
            energy=organism.energy,
            body_mass=organism.body_mass,
            mating_type=organism.mating_type,
        )
        for organism_id, organism in sorted(final_world.organisms.items())
    ) if final_frame.organisms else ()


def test_spatial_observation_does_not_change_fixed_seed_reference_outcomes() -> None:
    """Test an attached spatial observer is measurement-only."""
    config = ReferenceEcologyConfig(
        width=5,
        height=5,
        initial_population=5,
        max_steps=4,
        seed=91,
    )
    baseline = build_reference_ecology(config)
    spatial = SpatialRecorder()
    observed = build_reference_ecology(
        config,
        additional_observers=(spatial,),
    )

    baseline.engine.run(baseline.simulation)
    observed.engine.run(observed.simulation)

    assert observed.recorder.observations == baseline.recorder.observations
    assert observed.genetic_recorder.observations == (
        baseline.genetic_recorder.observations
    )
    assert observed.pedigree_recorder.records == baseline.pedigree_recorder.records
    assert observed.event_recorder.steps == baseline.event_recorder.steps
