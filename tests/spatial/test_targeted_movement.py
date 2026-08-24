"""Tests for target-directed movement policies."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.spatial.targeted_movement import (
    StraightLineTowardTarget,
    TargetedMovementModel,
)


def test_straight_line_reaches_target_within_max_speed() -> None:
    """Test a reachable target is reached exactly without overshoot."""
    displacement = StraightLineTowardTarget().choose_displacement(
        current_x=2,
        current_y=3,
        target_x=4,
        target_y=4,
        max_speed=3,
    )

    assert displacement == (2, 1)


def test_straight_line_approaches_distant_axis_aligned_target() -> None:
    """Test a distant target is approached by the available speed."""
    displacement = StraightLineTowardTarget().choose_displacement(
        current_x=1,
        current_y=1,
        target_x=8,
        target_y=1,
        max_speed=2,
    )

    assert displacement == (2, 0)


def test_straight_line_respects_euclidean_limit_for_diagonal_target() -> None:
    """Test integer projection remains inside the Euclidean speed disk."""
    dx, dy = StraightLineTowardTarget().choose_displacement(
        current_x=0,
        current_y=0,
        target_x=9,
        target_y=9,
        max_speed=2,
    )

    assert dx * dx + dy * dy <= 4
    assert dx >= 0
    assert dy >= 0
    assert dx + dy > 0


def test_straight_line_stays_when_already_at_target() -> None:
    """Test no displacement is produced when already at the target."""
    assert StraightLineTowardTarget().choose_displacement(
        current_x=3,
        current_y=3,
        target_x=3,
        target_y=3,
        max_speed=4,
    ) == (0, 0)


def test_straight_line_stays_when_max_speed_is_zero() -> None:
    """Test zero movement capability prevents target approach."""
    assert StraightLineTowardTarget().choose_displacement(
        current_x=1,
        current_y=1,
        target_x=2,
        target_y=1,
        max_speed=0,
    ) == (0, 0)


@pytest.mark.parametrize(
    ("current_x", "current_y", "target_x", "target_y", "max_speed"),
    [
        (-1, 0, 1, 1, 1),
        (0, -1, 1, 1, 1),
        (0, 0, -1, 1, 1),
        (0, 0, 1, -1, 1),
        (0, 0, 1, 1, -1),
    ],
)
def test_straight_line_rejects_negative_inputs(
    current_x: int,
    current_y: int,
    target_x: int,
    target_y: int,
    max_speed: int,
) -> None:
    """Test target-directed movement rejects negative coordinates and speed."""
    with pytest.raises(ValueError):
        StraightLineTowardTarget().choose_displacement(
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            max_speed=max_speed,
        )


def test_straight_line_rejects_noninteger_max_speed() -> None:
    """Test target-directed movement requires integer max speed."""
    with pytest.raises(TypeError):
        StraightLineTowardTarget().choose_displacement(
            current_x=0,
            current_y=0,
            target_x=1,
            target_y=1,
            max_speed=cast(int, 1.0),
        )


def test_targeted_movement_protocol_accepts_structural_implementation() -> None:
    """Test custom targeted movement models may use structural typing."""

    class CustomTargetedMovement:
        def choose_displacement(
            self,
            *,
            current_x,
            current_y,
            target_x,
            target_y,
            max_speed,
        ) -> tuple[int, int]:
            return (0, 0)

    assert isinstance(CustomTargetedMovement(), TargetedMovementModel)
