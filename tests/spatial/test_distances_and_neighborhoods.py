"""Tests for spatial distance metrics and neighborhoods."""

from __future__ import annotations

import pytest

from evo_engine.spatial.distances import (
    Chebyshev,
    Manhattan,
    SquaredEuclidean,
    ToroidalChebyshev,
    ToroidalManhattan,
    ToroidalSquaredEuclidean,
)
from evo_engine.spatial.neighborhoods import (
    Euclidean,
    Moore,
    SameCell,
    VonNeumann,
)


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        (Manhattan(), 7),
        (Chebyshev(), 4),
        (SquaredEuclidean(), 25),
    ],
)
def test_planar_distance_metrics(metric, expected: int) -> None:
    """Test the three integer-grid distance conventions."""
    assert (
        metric.distance(
            x1=0,
            y1=0,
            x2=3,
            y2=4,
            width=10,
            height=10,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        (ToroidalManhattan(), 2),
        (ToroidalChebyshev(), 1),
        (ToroidalSquaredEuclidean(), 2),
    ],
)
def test_toroidal_distance_uses_shortest_wrapped_path(metric, expected: int) -> None:
    """Test distances across opposite world edges."""
    assert (
        metric.distance(
            x1=0,
            y1=0,
            x2=9,
            y2=9,
            width=10,
            height=10,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("center", "other", "expected"),
    [
        ((1, 1), (1, 1), True),
        ((1, 1), (1, 2), False),
    ],
)
def test_same_cell(
    center: tuple[int, int],
    other: tuple[int, int],
    expected: bool,
) -> None:
    """Test exact-coordinate neighborhood membership."""
    assert (
        SameCell().contains(
            center_x=center[0],
            center_y=center[1],
            other_x=other[0],
            other_y=other[1],
            width=5,
            height=5,
        )
        is expected
    )


@pytest.mark.parametrize(
    ("neighborhood", "other", "expected"),
    [
        (VonNeumann(radius=2), (2, 0), True),
        (VonNeumann(radius=2), (2, 1), False),
        (Moore(radius=2), (2, 2), True),
        (Moore(radius=1), (2, 2), False),
        (Euclidean(radius=2), (1, 1), True),
        (Euclidean(radius=2), (2, 2), False),
    ],
)
def test_neighborhood_shapes(
    neighborhood,
    other: tuple[int, int],
    expected: bool,
) -> None:
    """Test neighborhood membership by metric and radius."""
    assert (
        neighborhood.contains(
            center_x=0,
            center_y=0,
            other_x=other[0],
            other_y=other[1],
            width=10,
            height=10,
        )
        is expected
    )


@pytest.mark.parametrize(
    "neighborhood",
    [
        VonNeumann(radius=1, toroidal=True),
        Moore(radius=1, toroidal=True),
        Euclidean(radius=1, toroidal=True),
    ],
)
def test_toroidal_neighborhoods_cross_world_edge(neighborhood) -> None:
    """Test wrapped neighborhood membership."""
    assert neighborhood.contains(
        center_x=0,
        center_y=0,
        other_x=9,
        other_y=0,
        width=10,
        height=10,
    )
