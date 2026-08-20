"""Tests for SimulationState."""

from __future__ import annotations

import random

from tests.helpers import add_organism, make_state


def test_copy_preserves_step_index() -> None:
    """Test that transactional copies start at the same simulation step."""
    state = make_state()
    state.step_index = 7

    copied = state.copy()

    assert copied.step_index == 7


def test_copy_shares_immutable_genetic_architecture() -> None:
    """Test that state copies reuse immutable model configuration."""
    state = make_state()

    copied = state.copy()

    assert copied.genetic_architecture is state.genetic_architecture


def test_copy_independently_copies_world() -> None:
    """Test that transactional world mutations do not affect authority."""
    state = make_state()
    add_organism(state, energy=20)

    copied = state.copy()
    copied.world.organisms[0].energy = 3

    assert state.world.organisms[0].energy == 20


def test_copy_preserves_rng_state_without_sharing_rng() -> None:
    """Test deterministic RNG cloning for transactional step execution."""
    state = make_state(seed=17)

    copied = state.copy()

    assert copied.rng is not state.rng
    assert copied.rng.random() == state.rng.random()


def test_copy_rng_advancement_is_independent() -> None:
    """Test that advancing a working RNG does not advance authority."""
    state = make_state(seed=11)
    expected = random.Random(11)

    copied = state.copy()
    copied.rng.random()

    assert state.rng.random() == expected.random()
