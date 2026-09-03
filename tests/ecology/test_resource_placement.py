"""Tests for renewable-resource spatial placement models."""

from __future__ import annotations

import random

import pytest

from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    UniformResourcePlacement,
)


def test_uniform_placement_replays_historical_rng_sequence() -> None:
    """Test uniform placement preserves the historical two-randrange sequence."""
    rng = random.Random(17)
    control = random.Random(17)
    placement = UniformResourcePlacement()

    positions = tuple(
        placement.choose_position(width=5, height=7, rng=rng) for _ in range(6)
    )
    expected = tuple((control.randrange(5), control.randrange(7)) for _ in range(6))

    assert positions == expected
    assert rng.getstate() == control.getstate()


def test_resource_patch_rejects_invalid_geometry_or_weight() -> None:
    """Test patch values reject negative geometry and nonpositive weights."""
    with pytest.raises(ValueError):
        ResourcePatch(center_x=-1, center_y=0)
    with pytest.raises(ValueError):
        ResourcePatch(center_x=0, center_y=-1)
    with pytest.raises(ValueError):
        ResourcePatch(center_x=0, center_y=0, radius=-1)
    with pytest.raises(ValueError):
        ResourcePatch(center_x=0, center_y=0, weight=0)


def test_patchy_placement_requires_at_least_one_patch() -> None:
    """Test patchy placement cannot be configured without spatial support."""
    with pytest.raises(ValueError, match="at least one ResourcePatch"):
        PatchyResourcePlacement(patches=())


def test_zero_radius_patch_always_places_at_its_center() -> None:
    """Test a radius-zero patch has exact one-cell semantics."""
    placement = PatchyResourcePlacement(
        patches=(ResourcePatch(center_x=2, center_y=3, radius=0),)
    )
    rng = random.Random(11)

    assert (
        tuple(placement.choose_position(width=6, height=7, rng=rng) for _ in range(5))
        == ((2, 3),) * 5
    )


def test_edge_patch_is_truncated_to_in_bounds_disk_cells() -> None:
    """Test edge patches sample only the in-world intersection of the disk."""
    placement = PatchyResourcePlacement(
        patches=(ResourcePatch(center_x=0, center_y=0, radius=2),)
    )
    rng = random.Random(23)
    expected_cells = {
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (0, 2),
    }

    positions = tuple(
        placement.choose_position(width=5, height=4, rng=rng) for _ in range(20)
    )

    assert set(positions) <= expected_cells


def test_multiple_patches_are_reproducible_and_never_place_between_patches() -> None:
    """Test weighted multi-patch placement is deterministic for a fixed seed."""
    placement = PatchyResourcePlacement(
        patches=(
            ResourcePatch(center_x=0, center_y=0, radius=0, weight=1),
            ResourcePatch(center_x=4, center_y=4, radius=0, weight=3),
        )
    )
    first_rng = random.Random(29)
    second_rng = random.Random(29)

    first = tuple(
        placement.choose_position(width=5, height=5, rng=first_rng) for _ in range(12)
    )
    second = tuple(
        placement.choose_position(width=5, height=5, rng=second_rng)
        for _ in range(12)
    )

    assert first == second
    assert set(first) <= {(0, 0), (4, 4)}
    assert (0, 0) in first
    assert (4, 4) in first


def test_patch_center_must_fit_the_runtime_world() -> None:
    """Test generic patch configuration fails clearly against a smaller world."""
    placement = PatchyResourcePlacement(
        patches=(ResourcePatch(center_x=5, center_y=1, radius=2),)
    )

    with pytest.raises(ValueError, match="must lie within world bounds"):
        placement.choose_position(
            width=5,
            height=5,
            rng=random.Random(31),
        )
