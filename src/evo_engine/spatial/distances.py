"""Distance metrics for integer-grid spatial simulation."""

from __future__ import annotations

from typing import Protocol


class DistanceMetric(Protocol):
    """Define a distance metric between two world coordinates."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the distance between two coordinates.

        Args:
            x1: First horizontal coordinate.
            y1: First vertical coordinate.
            x2: Second horizontal coordinate.
            y2: Second vertical coordinate.
            width: Width of the world.
            height: Height of the world.

        Returns:
            Distance between the coordinates.
        """
        ...


class Manhattan:
    """Measure Manhattan distance between coordinates."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the Manhattan distance between two coordinates."""
        return abs(x1 - x2) + abs(y1 - y2)


class Chebyshev:
    """Measure Chebyshev distance between coordinates."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the Chebyshev distance between two coordinates."""
        return max(
            abs(x1 - x2),
            abs(y1 - y2),
        )


class SquaredEuclidean:
    """Measure squared Euclidean distance between coordinates."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the squared Euclidean distance between two coordinates."""
        dx = x1 - x2
        dy = y1 - y2

        return dx * dx + dy * dy


class ToroidalManhattan:
    """Measure Manhattan distance on a toroidal world."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the toroidal Manhattan distance."""
        dx = _toroidal_axis_distance(
            x1,
            x2,
            size=width,
        )
        dy = _toroidal_axis_distance(
            y1,
            y2,
            size=height,
        )

        return dx + dy


class ToroidalChebyshev:
    """Measure Chebyshev distance on a toroidal world."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the toroidal Chebyshev distance."""
        dx = _toroidal_axis_distance(
            x1,
            x2,
            size=width,
        )
        dy = _toroidal_axis_distance(
            y1,
            y2,
            size=height,
        )

        return max(
            dx,
            dy,
        )


class ToroidalSquaredEuclidean:
    """Measure squared Euclidean distance on a toroidal world."""

    def distance(
        self,
        *,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        width: int,
        height: int,
    ) -> int:
        """Return the toroidal squared Euclidean distance."""
        dx = _toroidal_axis_distance(
            x1,
            x2,
            size=width,
        )
        dy = _toroidal_axis_distance(
            y1,
            y2,
            size=height,
        )

        return dx * dx + dy * dy


def _toroidal_axis_distance(
    first: int,
    second: int,
    *,
    size: int,
) -> int:
    """Return the shortest distance along one toroidal axis."""
    direct_distance = abs(first - second)

    return min(
        direct_distance,
        size - direct_distance,
    )
