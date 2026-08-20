"""Tests for movement-pattern policies."""

from __future__ import annotations

import random

import pytest

from evo_engine.spatial.movement_patterns import (
    GaussianRandom,
    MooreRandom,
    UniformRandom,
    VonNeumannRandom,
)


@pytest.mark.parametrize(
    "pattern",
    [
        UniformRandom(),
        VonNeumannRandom(),
        MooreRandom(),
        GaussianRandom(
            standard_deviation=3,
        ),
    ],
)
def test_zero_max_speed_prevents_displacement(pattern) -> None:
    """Test the biological immobility boundary across movement policies."""
    assert pattern.choose_displacement(
        rng=random.Random(1),
        max_speed=0,
    ) == (0, 0)


@pytest.mark.parametrize(
    "pattern",
    [
        UniformRandom(),
        VonNeumannRandom(),
        MooreRandom(),
        GaussianRandom(),
    ],
)
def test_movement_patterns_reject_negative_max_speed(pattern) -> None:
    """Test movement capability cannot be negative."""
    with pytest.raises(ValueError):
        pattern.choose_displacement(
            rng=random.Random(1),
            max_speed=-1,
        )


def test_uniform_random_stays_inside_euclidean_speed_limit() -> None:
    """Test uniform displacements stay inside the max-speed disk."""
    pattern = UniformRandom()
    rng = random.Random(1)

    for _ in range(200):
        dx, dy = pattern.choose_displacement(
            rng=rng,
            max_speed=3,
        )

        assert dx * dx + dy * dy <= 9


def test_von_neumann_random_moves_one_orthogonal_cell() -> None:
    """Test fixed-step orthogonal movement."""
    dx, dy = VonNeumannRandom().choose_displacement(
        rng=random.Random(1),
        max_speed=5,
    )

    assert abs(dx) + abs(dy) == 1


def test_moore_random_excludes_diagonal_when_max_speed_is_one() -> None:
    """Test diagonal adjacency respects Euclidean max speed."""
    pattern = MooreRandom()
    rng = random.Random(1)

    for _ in range(40):
        dx, dy = pattern.choose_displacement(
            rng=rng,
            max_speed=1,
        )

        assert dx * dx + dy * dy == 1


def test_moore_random_can_use_diagonal_when_speed_allows_it() -> None:
    """Test the Moore policy retains diagonal movement when legal."""
    pattern = MooreRandom()
    rng = random.Random(2)

    displacements = {
        pattern.choose_displacement(
            rng=rng,
            max_speed=2,
        )
        for _ in range(100)
    }

    assert any(abs(dx) == 1 and abs(dy) == 1 for dx, dy in displacements)


def test_gaussian_random_projects_to_euclidean_speed_limit() -> None:
    """Test Gaussian attempts cannot exceed organism max speed."""
    pattern = GaussianRandom(
        standard_deviation=100,
    )
    rng = random.Random(1)

    for _ in range(100):
        dx, dy = pattern.choose_displacement(
            rng=rng,
            max_speed=2,
        )

        assert dx * dx + dy * dy <= 4


def test_gaussian_random_rejects_negative_standard_deviation() -> None:
    """Test movement-distribution configuration validation."""
    with pytest.raises(ValueError):
        GaussianRandom(
            standard_deviation=-1,
        )
