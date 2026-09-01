"""Tests for movement-target selection models."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    FixedSensoryRange,
    MovementTarget,
    MovementTargetModel,
    NearestResourceTarget,
    NoMovementTarget,
    determine_movement_target,
)
from evo_engine.genetics.builtin_traits import SENSORY_RANGE
from tests.helpers import add_organism, make_state


def test_no_movement_target_never_selects_target() -> None:
    """Test the untargeted default leaves movement without a target."""
    state = make_state()
    organism = add_organism(state)

    assert (
        NoMovementTarget().choose_target(
            organism,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=state,
        )
        is None
    )


def test_nearest_resource_target_selects_nearest_detectable_resource() -> None:
    """Test resource targeting uses sensory range and nearest distance."""
    state = make_state(width=10, height=10)
    organism = add_organism(
        state,
        x=1,
        y=1,
    )
    state.domain_state.add_resources(x=3, y=1, amount=2)
    state.domain_state.add_resources(x=5, y=1, amount=20)
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=4),
    )

    target = model.choose_target(
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=state,
    )

    assert target == MovementTarget(x=3, y=1)


def test_nearest_resource_target_cannot_see_outside_sensory_range() -> None:
    """Test resource deposits beyond sensory radius are not targeted."""
    state = make_state(width=10, height=10)
    organism = add_organism(state, x=1, y=1)
    state.domain_state.add_resources(x=4, y=1, amount=5)
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=2),
    )

    assert (
        model.choose_target(
            organism,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=state,
        )
        is None
    )


def test_nearest_resource_target_ignores_other_behavioral_purposes() -> None:
    """Test resource sensing is skipped when the configured purpose is inactive."""

    class SensoryModelThatMustNotRun:
        def determine_range(self, organism, *, simulation_state) -> int:
            raise AssertionError("inactive targeting must not evaluate sensing")

    state = make_state()
    organism = add_organism(state)
    model = NearestResourceTarget(
        sensory_range_model=SensoryModelThatMustNotRun(),
    )

    assert (
        model.choose_target(
            organism,
            behavioral_purpose=EXPLORATION,
            simulation_state=state,
        )
        is None
    )


def test_nearest_resource_target_prefers_larger_equal_distance_deposit() -> None:
    """Test resource amount deterministically breaks equal-distance ties."""
    state = make_state(width=5, height=5)
    organism = add_organism(state, x=2, y=2)
    state.domain_state.add_resources(x=1, y=2, amount=3)
    state.domain_state.add_resources(x=3, y=2, amount=7)
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=2),
    )

    target = model.choose_target(
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=state,
    )

    assert target == MovementTarget(x=3, y=2)


def test_zero_sensory_range_detects_resource_on_current_cell() -> None:
    """Test zero range still includes the organism's current coordinate."""
    state = make_state(width=3, height=3)
    organism = add_organism(state, x=1, y=1)
    state.domain_state.add_resources(x=1, y=1, amount=3)
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=0),
    )

    assert model.choose_target(
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=state,
    ) == MovementTarget(x=1, y=1)


def test_nearest_resource_target_requires_sensory_trait_by_default() -> None:
    """Test trait-driven resource sensing propagates its nested requirement."""
    assert NearestResourceTarget().required_traits == frozenset({SENSORY_RANGE})


def test_fixed_sensory_range_removes_targeting_trait_requirement() -> None:
    """Test fixed sensing allows resource targeting without genetic sensing."""
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=3),
    )

    assert model.required_traits == frozenset()


def test_movement_target_protocol_accepts_structural_implementation() -> None:
    """Test custom target models need not inherit from engine classes."""

    class CustomTarget:
        def choose_target(
            self,
            organism,
            *,
            behavioral_purpose,
            simulation_state,
        ) -> MovementTarget | None:
            return None

    assert isinstance(CustomTarget(), MovementTargetModel)


def test_determine_movement_target_rejects_invalid_custom_return() -> None:
    """Test the targeting boundary validates custom model return types."""

    class InvalidTarget:
        def choose_target(
            self,
            organism,
            *,
            behavioral_purpose,
            simulation_state,
        ):
            return (1, 1)

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(TypeError):
        determine_movement_target(
            cast(MovementTargetModel, InvalidTarget()),
            organism,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=state,
        )


def test_determine_movement_target_rejects_out_of_bounds_target() -> None:
    """Test selected targets must lie inside the current world."""

    class OutOfBoundsTarget:
        def choose_target(
            self,
            organism,
            *,
            behavioral_purpose,
            simulation_state,
        ) -> MovementTarget:
            return MovementTarget(x=99, y=99)

    state = make_state(width=3, height=3)
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_movement_target(
            OutOfBoundsTarget(),
            organism,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=state,
        )
