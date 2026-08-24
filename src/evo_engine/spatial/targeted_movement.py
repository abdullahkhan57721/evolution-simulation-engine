"""Spatial policies for approaching a selected movement target."""

from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

from evo_engine.validation import validators


def _validate_targeted_movement_inputs(
    *,
    current_x: int,
    current_y: int,
    target_x: int,
    target_y: int,
    max_speed: int,
) -> None:
    """Validate target-directed movement coordinates and speed."""
    for name, value in (
        ("current_x", current_x),
        ("current_y", current_y),
        ("target_x", target_x),
        ("target_y", target_y),
        ("max_speed", max_speed),
    ):
        validators.validate_int_ge(
            value,
            bound=0,
            name=name,
        )


def _within_max_speed(
    dx: int,
    dy: int,
    max_speed: int,
) -> bool:
    """Return whether a displacement lies inside the Euclidean speed disk."""
    return dx * dx + dy * dy <= max_speed * max_speed


def _project_to_max_speed(
    dx: int,
    dy: int,
    max_speed: int,
) -> tuple[int, int]:
    """Project a nonzero displacement to the max-speed circle and round it."""
    scale = max_speed / math.hypot(dx, dy)
    return (
        round(dx * scale),
        round(dy * scale),
    )


def _move_component_toward_zero(value: int) -> int:
    """Move a nonzero integer component one unit toward zero."""
    return value - 1 if value > 0 else value + 1


def _correct_rounding_overshoot(
    dx: int,
    dy: int,
    max_speed: int,
) -> tuple[int, int]:
    """Shrink a rounded projection until it lies inside the speed disk."""
    while not _within_max_speed(
        dx,
        dy,
        max_speed,
    ):
        if abs(dx) >= abs(dy):
            dx = _move_component_toward_zero(dx)
        else:
            dy = _move_component_toward_zero(dy)

    return (
        dx,
        dy,
    )


@runtime_checkable
class TargetedMovementModel(Protocol):
    """Choose a displacement toward a selected target coordinate."""

    def choose_displacement(
        self,
        *,
        current_x: int,
        current_y: int,
        target_x: int,
        target_y: int,
        max_speed: int,
    ) -> tuple[int, int]:
        """Return a target-directed displacement within ``max_speed``.

        Args:
            current_x: Organism's current horizontal coordinate.
            current_y: Organism's current vertical coordinate.
            target_x: Target horizontal coordinate.
            target_y: Target vertical coordinate.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical integer displacement.
        """
        ...


class StraightLineTowardTarget:
    """Move directly toward a target without exceeding Euclidean max speed."""

    def choose_displacement(
        self,
        *,
        current_x: int,
        current_y: int,
        target_x: int,
        target_y: int,
        max_speed: int,
    ) -> tuple[int, int]:
        """Return a straight-line integer displacement toward the target.

        Targets within one timestep's movement capability are reached exactly.
        More distant targets are approached by projecting the target vector to
        the max-speed circle and rounding to the integer grid. Any rounding
        overshoot is corrected back inside the Euclidean speed limit.

        Args:
            current_x: Organism's current horizontal coordinate.
            current_y: Organism's current vertical coordinate.
            target_x: Target horizontal coordinate.
            target_y: Target vertical coordinate.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical integer displacement toward the target.

        Raises:
            TypeError: If a coordinate or max speed is not an integer.
            ValueError: If a coordinate or max speed is negative.
        """
        _validate_targeted_movement_inputs(
            current_x=current_x,
            current_y=current_y,
            target_x=target_x,
            target_y=target_y,
            max_speed=max_speed,
        )

        remaining_x = target_x - current_x
        remaining_y = target_y - current_y

        if max_speed == 0 or (remaining_x == 0 and remaining_y == 0):
            return (0, 0)

        if _within_max_speed(
            remaining_x,
            remaining_y,
            max_speed,
        ):
            return (
                remaining_x,
                remaining_y,
            )

        dx, dy = _project_to_max_speed(
            remaining_x,
            remaining_y,
            max_speed,
        )
        return _correct_rounding_overshoot(
            dx,
            dy,
            max_speed,
        )
