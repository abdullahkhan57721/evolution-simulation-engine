"""Tests for resource-landscape composition in the reference ecology."""

from __future__ import annotations

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    UniformResourcePlacement,
)
from evo_engine.observation import SpatialRecorder
from evo_engine.presets import ReferenceEcologyConfig
from evo_engine.presets.reference_ecology.builders import (
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.processes import ResourceGeneration


def _reference_resource_generation(config: ReferenceEcologyConfig) -> ResourceGeneration:
    engine = build_reference_engine(config)
    for stage in engine.step_coordinator.stages:
        for process in stage.processes:
            if isinstance(process, ResourceGeneration):
                return process
    raise AssertionError("reference engine has no ResourceGeneration process")


def test_reference_config_defaults_to_uniform_resource_placement() -> None:
    """Test the ordinary reference baseline remains explicitly uniform."""
    config = ReferenceEcologyConfig()

    assert isinstance(config.resource_placement_model, UniformResourcePlacement)
    assert _reference_resource_generation(config).placement_model is (
        config.resource_placement_model
    )


def test_reference_engine_wires_configured_patchy_placement() -> None:
    """Test reference configuration composes patch placement without rewiring."""
    placement = PatchyResourcePlacement(
        patches=(ResourcePatch(center_x=11, center_y=11, radius=0),)
    )
    config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=1,
        seed=53,
        resource_placement_model=placement,
    )

    assert _reference_resource_generation(config).placement_model is placement


def test_patchy_reference_run_is_recorded_by_existing_spatial_observation() -> None:
    """Test committed patch geography appears without observation schema changes."""
    placement = PatchyResourcePlacement(
        patches=(ResourcePatch(center_x=11, center_y=11, radius=0),)
    )
    config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=1,
        seed=59,
        resource_placement_model=placement,
    )
    recorder = SpatialRecorder()
    simulation = build_reference_simulation(config)
    engine = build_reference_engine(config, observers=(recorder,))

    engine.run(simulation)

    assert len(recorder.observations) == 2
    assert recorder.observations[0].resources == ()
    assert len(recorder.observations[1].resources) == 1
    resource = recorder.observations[1].resources[0]
    assert (resource.x, resource.y) == (11, 11)
    assert resource.amount == (
        config.resource_generation_amount * config.resource_deposits_per_step
    )


def test_patchy_reference_spatial_history_replays_for_fixed_seed() -> None:
    """Test a fixed reference seed reproduces the complete resource history."""
    config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=3,
        seed=61,
        resource_placement_model=PatchyResourcePlacement(
            patches=(
                ResourcePatch(center_x=2, center_y=9, radius=1, weight=1),
                ResourcePatch(center_x=9, center_y=2, radius=1, weight=2),
            )
        ),
    )

    first_recorder = SpatialRecorder()
    first_simulation = build_reference_simulation(config)
    build_reference_engine(config, observers=(first_recorder,)).run(first_simulation)

    second_recorder = SpatialRecorder()
    second_simulation = build_reference_simulation(config)
    build_reference_engine(config, observers=(second_recorder,)).run(second_simulation)

    assert first_recorder.observations == second_recorder.observations
