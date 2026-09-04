"""Tests for the minimal controlled locomotion lifecycle composition."""

from __future__ import annotations

from evo_engine.experiments.locomotion import measure_applied_movement
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import EventRecorder
from evo_engine.presets.controlled_locomotion import (
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.processes import Movement, Reproduction, ResourceConsumption
from evo_engine.telemetry import AppliedEvent
from evo_engine.world import WorldState


def _run_one_step(
    *,
    max_speed: int,
    target_x: int,
    target_y: int,
    start_x: int = 5,
    start_y: int = 5,
    seed: int = 17,
) -> tuple[ControlledLocomotionConfig, WorldState, tuple[AppliedEvent, ...]]:
    config = ControlledLocomotionConfig(
        width=31,
        height=31,
        max_steps=1,
        seed=seed,
        founders=(
            ControlledLocomotionFounder(
                max_speed=max_speed,
                x=start_x,
                y=start_y,
            ),
        ),
        resource_deposits=(
            ControlledResourceDeposit(x=target_x, y=target_y, amount=100),
        ),
        reproduction_minimum_energy=10_000,
    )
    recorder = EventRecorder()
    spec = build_controlled_locomotion_spec(
        config,
        telemetry_observers=(recorder,),
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)
    return config, compiled.simulation.state.domain_state, recorder.events


def test_controlled_locomotion_spec_compiles_with_only_focal_genetic_trait() -> None:
    """Test the reusable composition satisfies biological dependency preflight."""
    spec = build_controlled_locomotion_spec()

    compiled = spec.compile()

    assert not compiled.dependency_report.missing
    assert spec.genetic_architecture.trait_names == frozenset({MAX_SPEED})


def test_higher_capacity_permits_greater_target_directed_displacement() -> None:
    """Test inherited max speed changes capacity rather than an abstract score."""
    _, _, slow_events = _run_one_step(max_speed=2, target_x=25, target_y=5)
    _, _, fast_events = _run_one_step(max_speed=5, target_x=25, target_y=5)

    slow_event = next(
        event for event in slow_events if isinstance(event.event, Movement.Event)
    )
    fast_event = next(
        event for event in fast_events if isinstance(event.event, Movement.Event)
    )
    slow_movement = slow_event.event
    fast_movement = fast_event.event
    assert isinstance(slow_movement, Movement.Event)
    assert isinstance(fast_movement, Movement.Event)
    slow = measure_applied_movement(slow_event)
    fast = measure_applied_movement(fast_event)

    assert slow_movement.target_x == 25
    assert fast_movement.target_x == 25
    assert slow.realized_distance == 2.0
    assert fast.realized_distance == 5.0
    assert slow.locomotion_energy_expenditure == 4
    assert fast.locomotion_energy_expenditure == 25


def test_target_within_capacity_is_reached_without_overshoot_and_consumed_locally() -> (
    None
):
    """Test endpoint feeding follows exact target arrival rather than path traversal."""
    _, world, events = _run_one_step(max_speed=10, target_x=8, target_y=9)

    movement_applied = next(
        event for event in events if isinstance(event.event, Movement.Event)
    )
    feeding_applied = next(
        event for event in events if isinstance(event.event, ResourceConsumption.Event)
    )
    movement = movement_applied.event
    feeding = feeding_applied.event
    assert isinstance(movement, Movement.Event)
    assert isinstance(feeding, ResourceConsumption.Event)
    measured = measure_applied_movement(movement_applied)

    assert (movement.dx, movement.dy) == (3, 4)
    assert (movement.new_x, movement.new_y) == (8, 9)
    assert measured.realized_distance == 5.0
    assert measured.locomotion_energy_expenditure == 25
    assert (feeding.x, feeding.y) == (8, 9)
    assert world.organisms[0].x == 8
    assert world.organisms[0].y == 9


def test_no_resource_target_produces_stationary_fallback_not_blind_travel() -> None:
    """Test depleted landscapes cannot trigger multi-cell random exploration."""
    config = ControlledLocomotionConfig(
        width=20,
        height=20,
        max_steps=2,
        founders=(ControlledLocomotionFounder(max_speed=8, x=5, y=5),),
        resource_deposits=(ControlledResourceDeposit(x=6, y=5, amount=1),),
        resource_request_amount=1,
        reproduction_minimum_energy=10_000,
    )
    recorder = EventRecorder()
    spec = build_controlled_locomotion_spec(
        config,
        telemetry_observers=(recorder,),
    )
    compiled = spec.compile()

    compiled.engine.run(compiled.simulation)

    movement_applied = tuple(
        event for event in recorder.events if isinstance(event.event, Movement.Event)
    )
    assert len(movement_applied) == 2
    first = movement_applied[0].event
    second = movement_applied[1].event
    assert isinstance(first, Movement.Event)
    assert isinstance(second, Movement.Event)
    assert first.target_x == 6
    assert (first.dx, first.dy) == (1, 0)
    assert second.target_x is None
    assert (second.dx, second.dy) == (0, 0)


def test_single_parent_reproduction_clones_capacity_without_mate_search() -> None:
    """Test reproduction propagates one parent and movement stays food-directed."""
    config = ControlledLocomotionConfig(
        width=15,
        height=15,
        max_steps=1,
        founders=(ControlledLocomotionFounder(max_speed=3, x=7, y=7),),
        resource_deposits=(ControlledResourceDeposit(x=7, y=7, amount=100),),
        initial_energy=100,
        resource_request_amount=20,
        reproduction_minimum_energy=100,
        reproduction_energy_investment=20,
    )
    recorder = EventRecorder()
    spec = build_controlled_locomotion_spec(
        config,
        telemetry_observers=(recorder,),
    )
    compiled = spec.compile()

    compiled.engine.run(compiled.simulation)

    reproduction_applied = next(
        event
        for event in recorder.events
        if isinstance(event.event, Reproduction.Event)
    )
    movement_applied = next(
        event for event in recorder.events if isinstance(event.event, Movement.Event)
    )
    reproduction = reproduction_applied.event
    movement = movement_applied.event
    assert isinstance(reproduction, Reproduction.Event)
    assert isinstance(movement, Movement.Event)
    world = compiled.simulation.state.domain_state

    assert reproduction.parent_ids == (0,)
    assert reproduction.participant_ids == (0,)
    assert movement.behavioral_purpose == "energy_acquisition"
    assert movement.target_x == 7
    assert len(world.organisms) == 2
    assert world.organisms[1].genetic_phenotype.int_value(MAX_SPEED) == 3
    assert world.organisms[1].body_mass == config.body_mass
