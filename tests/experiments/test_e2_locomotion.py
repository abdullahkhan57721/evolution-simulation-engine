"""Tests for E2 controlled-locomotion mechanics assays and diagnostics."""

from __future__ import annotations

import math

from evo_engine.experiments.e2_locomotion import (
    LocomotionMechanicsCase,
    run_locomotion_bearing_assay,
    run_locomotion_mechanics_case,
)
from evo_engine.observation import EventRecorder
from evo_engine.presets.controlled_locomotion import (
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.processes import ResourceConsumption


def test_bearing_assay_quantifies_grid_rounding_anisotropy() -> None:
    """Test equal capacity can realize different distances at different bearings."""
    outcomes = run_locomotion_bearing_assay(
        max_speed=5,
        target_offsets=((20, 0), (20, 10), (20, 20), (10, 20), (0, 20)),
    )

    realized = tuple(outcome.measurement.realized_distance for outcome in outcomes)

    assert all(distance <= 5.0 for distance in realized)
    assert max(realized) > min(realized)
    assert math.isclose(min(realized), math.sqrt(20.0))
    assert math.isclose(max(realized), 5.0)


def test_quadratic_use_cost_matches_attempted_grid_displacement() -> None:
    """Test default cost equals squared Euclidean attempted travel at unit coefficient."""
    outcomes = run_locomotion_bearing_assay(
        max_speed=5,
        target_offsets=((20, 0), (20, 10), (20, 20)),
    )

    for outcome in outcomes:
        expected_cost = outcome.attempted_dx**2 + outcome.attempted_dy**2
        assert outcome.measurement.locomotion_energy_expenditure == expected_cost


def test_canonical_targeted_assay_has_no_boundary_clipping() -> None:
    """Test padded in-bounds targets keep attempted and realized travel aligned."""
    outcomes = run_locomotion_bearing_assay(
        max_speed=7,
        target_offsets=((25, 0), (-25, 0), (20, 15), (-20, -15)),
    )

    for outcome in outcomes:
        assert math.isclose(
            outcome.measurement.attempted_distance,
            outcome.measurement.realized_distance,
        )


def test_short_target_is_reached_exactly_even_when_capacity_is_higher() -> None:
    """Test capacity is a ceiling rather than mandatory realized displacement."""
    outcome = run_locomotion_mechanics_case(
        LocomotionMechanicsCase(max_speed=12, target_dx=3, target_dy=4)
    )

    assert outcome.target_reached
    assert (outcome.attempted_dx, outcome.attempted_dy) == (3, 4)
    assert outcome.measurement.realized_distance == 5.0


def test_scarce_resource_winner_is_seed_randomized_not_fixed_to_low_id() -> None:
    """Test competition ordering does not encode a permanent organism-ID winner."""
    winners: set[int] = set()
    for seed in range(20):
        config = ControlledLocomotionConfig(
            width=10,
            height=10,
            max_steps=1,
            seed=seed,
            founders=(
                ControlledLocomotionFounder(max_speed=0, x=5, y=5),
                ControlledLocomotionFounder(max_speed=0, x=5, y=5),
            ),
            resource_deposits=(
                ControlledResourceDeposit(x=5, y=5, amount=1),
            ),
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
        feeding = tuple(
            event.event
            for event in recorder.events
            if isinstance(event.event, ResourceConsumption.Event)
        )
        assert len(feeding) == 1
        winners.add(feeding[0].organism_id)

    assert winners == {0, 1}
