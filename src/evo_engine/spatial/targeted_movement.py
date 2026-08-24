"""Spatial policies for approaching a selected movement target."""

from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

from evo_engine.validation import validators


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

        remaining_x = target_x - current_x
        remaining_y = target_y - current_y
        distance_squared = remaining_x * remaining_x + remaining_y * remaining_y

        if max_speed == 0 or distance_squared == 0:
            return (0, 0)

        if distance_squared <= max_speed * max_speed:
            return (
                remaining_x,
                remaining_y,
            )

        distance = math.sqrt(distance_squared)
        scale = max_speed / distance
        dx = round(remaining_x * scale)
        dy = round(remaining_y * scale)

        while dx * dx + dy * dy > max_speed * max_speed:
            if abs(dx) >= abs(dy):
                dx -= 1 if dx > 0 else -1
            else:
                dy -= 1 if dy > 0 else -1

        if dx == 0 and dy == 0:
            if abs(remaining_x) >= abs(remaining_y):
                dx = 1 if remaining_x > 0 else -1
            else:
                dy = 1 if remaining_y > 0 else -1

        return (
            dx,
            dy,
        )
