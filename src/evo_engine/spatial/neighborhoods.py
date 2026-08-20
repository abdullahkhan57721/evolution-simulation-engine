"""Neighborhood definitions for integer-grid spatial simulation."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.spatial.distances import (
    Chebyshev,
    Manhattan,
    SquaredEuclidean,
    ToroidalChebyshev,
    ToroidalManhattan,
    ToroidalSquaredEuclidean,
)
from evo_engine.validation import attrs_validators


class Neighborhood(Protocol):
    """Define whether two coordinates belong to the same neighborhood."""

    def contains(
        self,
        *,
        center_x: int,
        center_y: int,
        other_x: int,
        other_y: int,
        width: int,
        height: int,
    ) -> bool:
        """Return whether another coordinate is in the neighborhood.

        Args:
            center_x: Neighborhood center horizontal coordinate.
            center_y: Neighborhood center vertical coordinate.
            other_x: Other horizontal coordinate.
            other_y: Other vertical coordinate.
            width: Width of the world.
            height: Height of the world.

        Returns:
            Whether the other coordinate is in the neighborhood.
        """
        ...


class SameCell:
    """Include only coordinates occupying the same grid cell."""

    def contains(
        self,
        *,
        center_x: int,
        center_y: int,
        other_x: int,
        other_y: int,
        width: int,
        height: int,
    ) -> bool:
        """Return whether both coordinates occupy the same cell."""
        return center_x == other_x and center_y == other_y


@attrs.frozen(slots=True, kw_only=True)
class VonNeumann:
    """Define a Manhattan-distance neighborhood.

    Attributes:
        radius: Maximum Manhattan distance from the center.
        toroidal: Whether distance wraps around world boundaries.
    """

    radius: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    toroidal: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    def contains(
        self,
        *,
        center_x: int,
        center_y: int,
        other_x: int,
        other_y: int,
        width: int,
        height: int,
    ) -> bool:
        """Return whether a coordinate is in the neighborhood."""
        metric = ToroidalManhattan() if self.toroidal else Manhattan()

        distance = metric.distance(
            x1=center_x,
            y1=center_y,
            x2=other_x,
            y2=other_y,
            width=width,
            height=height,
        )

        return distance <= self.radius


@attrs.frozen(slots=True, kw_only=True)
class Moore:
    """Define a Chebyshev-distance neighborhood.

    Attributes:
        radius: Maximum Chebyshev distance from the center.
        toroidal: Whether distance wraps around world boundaries.
    """

    radius: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    toroidal: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    def contains(
        self,
        *,
        center_x: int,
        center_y: int,
        other_x: int,
        other_y: int,
        width: int,
        height: int,
    ) -> bool:
        """Return whether a coordinate is in the neighborhood."""
        metric = ToroidalChebyshev() if self.toroidal else Chebyshev()

        distance = metric.distance(
            x1=center_x,
            y1=center_y,
            x2=other_x,
            y2=other_y,
            width=width,
            height=height,
        )

        return distance <= self.radius


@attrs.frozen(slots=True, kw_only=True)
class Euclidean:
    """Define an approximately circular Euclidean neighborhood.

    Attributes:
        radius: Maximum Euclidean radius from the center.
        toroidal: Whether distance wraps around world boundaries.
    """

    radius: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    toroidal: bool = attrs.field(
        default=False,
        validator=attrs.validators.instance_of(bool),
    )

    def contains(
        self,
        *,
        center_x: int,
        center_y: int,
        other_x: int,
        other_y: int,
        width: int,
        height: int,
    ) -> bool:
        """Return whether a coordinate is in the neighborhood."""
        metric = ToroidalSquaredEuclidean() if self.toroidal else SquaredEuclidean()

        squared_distance = metric.distance(
            x1=center_x,
            y1=center_y,
            x2=other_x,
            y2=other_y,
            width=width,
            height=height,
        )

        return squared_distance <= self.radius * self.radius
