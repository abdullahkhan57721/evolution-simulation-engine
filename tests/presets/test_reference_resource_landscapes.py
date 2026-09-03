"""Tests for resource-landscape composition in the reference ecology."""

from __future__ import annotations

import pytest

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    UniformResourcePlacement,
)
from evo_engine.engine import SequentialStepCoordinator
from evo_engine.observation import EventRecorder, SpatialRecorder
from evo_engine.presets import ReferenceEcologyConfig, ReferenceTraitValues
from evo_engine.presets.reference_ecology.builders import (
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.processes import ResourceGeneration


def _reference_resource_generation(
    config: ReferenceEcologyConfig,
) -> ResourceGeneration:
    engine = build_reference_engine(config)
    coordinator = engine.step_coordinator
    if not isinstance(coordinator, SequentialStepCoordinator):
        raise AssertionError("reference engine must use SequentialStepCoordinator")

    for stage in coordinator.stages:
        for process in stage.processes:
            if isinstance(process, ResourceGeneration):
                return process
    raise AssertionError("reference engine has no ResourceGeneration process")


def _run_spatial_history(config: ReferenceEcologyConfig) -> SpatialRecorder:
    recorder = SpatialRecorder()
    simulation = build_reference_simulation(config)
    build_reference_engine(config, observers=(recorder,)).run(simulation)
    return recorder


def test_reference_config_defaults_to_uniform_resource_placement() -> None:
    """Test the ordinary reference baseline remains explicitly uniform."""
    config = ReferenceEcologyConfig()

    assert isinstance(config.resource_placement_model, UniformResourcePlacement)
    assert _reference_resource_generation(config).placement_model is (
        config.resource_placement_model
    )


def test_reference_config_rejects_invalid_resource_placement_model() -> None:
    """Test the reference preset validates the structural placement contract."""
    with pytest.raises(TypeError, match="resource_placement_model"):
        ReferenceEcologyConfig(resource_placement_model=object())  # type: ignore[arg-type]


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


def test_uniform_and_patchy_reference_runs_generate_equal_total_resource() -> None:
    """Test landscape geometry changes without changing configured generation."""
    uniform_config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=1,
        seed=57,
        resource_request_amount=0,
    )
    patchy_config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=1,
        seed=57,
        resource_request_amount=0,
        resource_placement_model=PatchyResourcePlacement(
            patches=(ResourcePatch(center_x=11, center_y=11, radius=0),)
        ),
    )
    uniform = _run_spatial_history(uniform_config)
    patchy = _run_spatial_history(patchy_config)

    uniform_resources = uniform.observations[-1].resources
    patchy_resources = patchy.observations[-1].resources
    expected_total = (
        uniform_config.resource_generation_amount
        * uniform_config.resource_deposits_per_step
    )

    assert sum(resource.amount for resource in uniform_resources) == expected_total
    assert sum(resource.amount for resource in patchy_resources) == expected_total
    assert uniform_resources != patchy_resources
    assert {(resource.x, resource.y) for resource in patchy_resources} == {(11, 11)}


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
    recorder = _run_spatial_history(config)

    assert len(recorder.observations) == 2
    assert recorder.observations[0].resources == ()
    assert len(recorder.observations[1].resources) == 1
    resource = recorder.observations[1].resources[0]
    assert (resource.x, resource.y) == (11, 11)
    assert resource.amount == (
        config.resource_generation_amount * config.resource_deposits_per_step
    )


def test_patchy_reference_run_keeps_movement_and_consumption_pipeline_active() -> None:
    """Test existing movement and consumption stages commit under patchiness."""
    config = ReferenceEcologyConfig(
        initial_population=1,
        max_steps=1,
        seed=60,
        traits=ReferenceTraitValues(max_speed=0),
        resource_placement_model=PatchyResourcePlacement(
            patches=(ResourcePatch(center_x=0, center_y=0, radius=0),)
        ),
    )
    recorder = EventRecorder()
    simulation = build_reference_simulation(config)
    build_reference_engine(config, telemetry_observers=(recorder,)).run(simulation)

    assert recorder.events_for_process("Movement")
    assert recorder.events_for_process("ResourceConsumption")


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

    first = _run_spatial_history(config)
    second = _run_spatial_history(config)

    assert first.observations == second.observations
