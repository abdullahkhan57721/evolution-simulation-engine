"""Tests for general mating-type compatibility and offspring assignment."""

from __future__ import annotations

import random

import pytest

from evo_engine.reproduction import (
    DifferentMatingTypes,
    FixedMatingType,
    RandomMatingType,
    determine_offspring_mating_type,
)
from tests.helpers import make_organism, make_state


def test_different_mating_types_accepts_unlike_labels() -> None:
    """Test compatibility depends on mating-type identity, not label semantics."""
    state = make_state()
    first = make_organism(mating_type="alpha")
    second = make_organism(mating_type="beta")

    assert DifferentMatingTypes()(first, second, state) is True


def test_different_mating_types_rejects_matching_labels() -> None:
    """Test organisms sharing a mating type are incompatible under the rule."""
    state = make_state()
    first = make_organism(mating_type="alpha")
    second = make_organism(mating_type="alpha")

    assert DifferentMatingTypes()(first, second, state) is False


def test_fixed_mating_type_does_not_advance_rng() -> None:
    """Test deterministic assignment leaves the simulation RNG untouched."""
    state = make_state(seed=17)
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())

    mating_type = determine_offspring_mating_type(
        FixedMatingType(mating_type="worker"),
        (make_organism(),),
        simulation_state=state,
        rng=state.rng,
    )

    assert mating_type == "worker"
    assert state.rng.random() == expected_rng.random()


def test_random_mating_type_uses_supplied_rng() -> None:
    """Test stochastic assignment is reproducible from the supplied RNG state."""
    state = make_state(seed=23)
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())
    model = RandomMatingType(mating_types=("alpha", "beta", "gamma"))

    actual = determine_offspring_mating_type(
        model,
        (make_organism(),),
        simulation_state=state,
        rng=state.rng,
    )

    assert actual == expected_rng.choice(model.mating_types)
    assert state.rng.random() == expected_rng.random()


@pytest.mark.parametrize(
    "mating_types",
    [
        (),
        ("alpha", "alpha"),
        ("", "beta"),
        ("   ", "beta"),
    ],
)
def test_random_mating_type_rejects_invalid_type_sets(
    mating_types: tuple[str, ...],
) -> None:
    """Test random assignment requires unique nonempty labels."""
    with pytest.raises(ValueError):
        RandomMatingType(mating_types=mating_types)
