"""Tests for spatial boundary conditions."""

from __future__ import annotations

import pytest

from evo_engine.spatial.boundary_conditions import (
    Clamped,
    Reflective,
    Rejecting,
    Toroidal,
)


@pytest.mark.parametrize(
    ("proposed_x", "proposed_y", "expected"),
    [
        (5, 5, (0, 0)),
        (-1, -1, (4, 4)),
        (6, -2, (1, 3)),
    ],
)
def test_toroidal_wraps_coordinates(
    proposed_x: int,
    proposed_y: int,
    expected: tuple[int, int],
) -> None:
    """Test modular boundary wrapping."""
    result = Toroidal().resolve(
        current_x=2,
        current_y=2,
        proposed_x=proposed_x,
        proposed_y=proposed_y,
        width=5,
        height=5,
    )

    assert result == expected


@pytest.mark.parametrize(
    ("proposed_x", "proposed_y", "expected"),
    [
        (-2, 3, (0, 3)),
        (8, -1, (4, 0)),
        (2, 2, (2, 2)),
    ],
)
def test_clamped_limits_to_nearest_boundary(
    proposed_x: int,
    proposed_y: int,
    expected: tuple[int, int],
) -> None:
    """Test coordinate clamping."""
    assert (
        Clamped().resolve(
            current_x=1,
            current_y=1,
            proposed_x=proposed_x,
            proposed_y=proposed_y,
            width=5,
            height=5,
        )
        == expected
    )


def test_rejecting_keeps_current_position_for_out_of_bounds_move() -> None:
    """Test rejection of invalid destinations."""
    assert Rejecting().resolve(
        current_x=2,
        current_y=3,
        proposed_x=5,
        proposed_y=3,
        width=5,
        height=5,
    ) == (2, 3)


def test_rejecting_accepts_valid_destination() -> None:
    """Test valid moves pass through unchanged."""
    assert Rejecting().resolve(
        current_x=2,
        current_y=3,
        proposed_x=4,
        proposed_y=0,
        width=5,
        height=5,
    ) == (4, 0)


@pytest.mark.parametrize(
    ("coordinate", "expected"),
    [
        (-1, 1),
        (-2, 2),
        (4, 4),
        (5, 3),
        (6, 2),
        (9, 1),
    ],
)
def test_reflective_handles_large_crossings(
    coordinate: int,
    expected: int,
) -> None:
    """Test repeated reflection over a bounded axis."""
    assert (
        Reflective._reflect(
            coordinate,
            size=5,
        )
        == expected
    )


def test_reflective_single_cell_axis_is_always_zero() -> None:
    """Test the degenerate one-cell reflective boundary."""
    assert (
        Reflective._reflect(
            100,
            size=1,
        )
        == 0
    )
