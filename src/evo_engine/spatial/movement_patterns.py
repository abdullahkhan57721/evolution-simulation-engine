"""Movement patterns for spatial simulation."""

from __future__ import annotations

import math
import random
from typing import Protocol

import attrs

from evo_engine.validation import attrs_validators, validators


def _validate_max_speed(max_speed: int) -> int:
    """Validate and return a nonnegative integer max speed."""
    return validators.validate_int_ge(
        max_speed,
        bound=0,
        name="max_speed",
    )


def _within_max_speed(
    dx: int,
    dy: int,
    max_speed: int,
) -> bool:
    """Return whether a displacement is within the Euclidean speed limit."""
    return dx * dx + dy * dy <= max_speed * max_speed


class MovementPattern(Protocol):
    """Define how an organism chooses a movement displacement."""

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Choose a movement displacement within an organism's max speed.

        Args:
            rng: Simulation random-number generator.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical integer displacement.
        """
        ...


class UniformRandom:
    """Choose uniformly from integer displacements inside a speed disk."""

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Choose a uniformly sampled integer displacement.

        Rejection sampling converts the bounding square into the integer grid
        points whose Euclidean magnitude does not exceed ``max_speed``.

        Args:
            rng: Simulation random-number generator.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical displacement.
        """
        _validate_max_speed(max_speed)

        if max_speed == 0:
            return (0, 0)

        while True:
            dx = rng.randint(
                -max_speed,
                max_speed,
            )
            dy = rng.randint(
                -max_speed,
                max_speed,
            )

            if _within_max_speed(
                dx,
                dy,
                max_speed,
            ):
                return (dx, dy)


class VonNeumannRandom:
    """Choose one orthogonally adjacent grid cell when movement is possible."""

    _DISPLACEMENTS = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    )

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Choose a one-cell orthogonal displacement.

        Args:
            rng: Simulation random-number generator.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical displacement.
        """
        _validate_max_speed(max_speed)

        if max_speed == 0:
            return (0, 0)

        return rng.choice(self._DISPLACEMENTS)


class MooreRandom:
    """Choose one adjacent grid cell permitted by the max speed."""

    _DISPLACEMENTS = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Choose an adjacent displacement within the Euclidean speed limit.

        At ``max_speed == 1``, diagonal moves are excluded because their
        Euclidean distance is greater than one grid unit.

        Args:
            rng: Simulation random-number generator.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical displacement.
        """
        _validate_max_speed(max_speed)

        if max_speed == 0:
            return (0, 0)

        valid_displacements = tuple(
            displacement
            for displacement in self._DISPLACEMENTS
            if _within_max_speed(
                displacement[0],
                displacement[1],
                max_speed,
            )
        )

        return rng.choice(valid_displacements)


@attrs.frozen(slots=True, kw_only=True)
class GaussianRandom:
    """Choose a Gaussian-distributed displacement within a speed limit.

    Attributes:
        standard_deviation: Standard deviation of each sampled axis.
    """

    standard_deviation: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Choose a bounded Gaussian-distributed integer displacement.

        Samples outside the speed disk are projected back toward the boundary.
        This preserves ``max_speed`` as a hard Euclidean capability limit
        without making the movement process depend on Gaussian details.

        Args:
            rng: Simulation random-number generator.
            max_speed: Maximum Euclidean grid-distance per timestep.

        Returns:
            Horizontal and vertical displacement.
        """
        _validate_max_speed(max_speed)

        if max_speed == 0:
            return (0, 0)

        dx = round(
            rng.gauss(
                0,
                self.standard_deviation,
            )
        )
        dy = round(
            rng.gauss(
                0,
                self.standard_deviation,
            )
        )

        if _within_max_speed(
            dx,
            dy,
            max_speed,
        ):
            return (dx, dy)

        distance = math.hypot(
            dx,
            dy,
        )
        scale = max_speed / distance
        dx = round(dx * scale)
        dy = round(dy * scale)

        # Rounding a projected vector can move it just outside the disk. Move
        # the larger component toward zero until the integer vector is valid.
        while not _within_max_speed(
            dx,
            dy,
            max_speed,
        ):
            if abs(dx) >= abs(dy):
                dx -= 1 if dx > 0 else -1
            else:
                dy -= 1 if dy > 0 else -1

        return (dx, dy)
