"""Boundary conditions for spatial simulation."""

from __future__ import annotations

from typing import Protocol


class BoundaryCondition(Protocol):
    """Define how attempted movement interacts with world boundaries."""

    def resolve(
        self,
        *,
        current_x: int,
        current_y: int,
        proposed_x: int,
        proposed_y: int,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Resolve an attempted destination.

        Args:
            current_x: Current horizontal coordinate.
            current_y: Current vertical coordinate.
            proposed_x: Proposed horizontal coordinate.
            proposed_y: Proposed vertical coordinate.
            width: Width of the world.
            height: Height of the world.

        Returns:
            Resolved valid world coordinate.
        """
        ...


class Toroidal:
    """Wrap movement around opposite world boundaries."""

    def resolve(
        self,
        *,
        current_x: int,
        current_y: int,
        proposed_x: int,
        proposed_y: int,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Resolve movement using toroidal wrapping."""
        return (
            proposed_x % width,
            proposed_y % height,
        )


class Clamped:
    """Clamp movement to the nearest world boundary."""

    def resolve(
        self,
        *,
        current_x: int,
        current_y: int,
        proposed_x: int,
        proposed_y: int,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Resolve movement by clamping the destination."""
        return (
            min(max(proposed_x, 0), width - 1),
            min(max(proposed_y, 0), height - 1),
        )


class Rejecting:
    """Reject movements whose destination lies outside the world."""

    def resolve(
        self,
        *,
        current_x: int,
        current_y: int,
        proposed_x: int,
        proposed_y: int,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Resolve movement by rejecting invalid destinations."""
        if not (0 <= proposed_x < width and 0 <= proposed_y < height):
            return (
                current_x,
                current_y,
            )

        return (
            proposed_x,
            proposed_y,
        )


class Reflective:
    """Reflect movement at world boundaries."""

    def resolve(
        self,
        *,
        current_x: int,
        current_y: int,
        proposed_x: int,
        proposed_y: int,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Resolve movement using reflective boundaries."""
        return (
            self._reflect(
                proposed_x,
                size=width,
            ),
            self._reflect(
                proposed_y,
                size=height,
            ),
        )

    @staticmethod
    def _reflect(
        coordinate: int,
        *,
        size: int,
    ) -> int:
        """Reflect one coordinate into a bounded interval."""
        if size == 1:
            return 0

        period = 2 * (size - 1)
        coordinate %= period

        if coordinate >= size:
            coordinate = period - coordinate

        return coordinate
