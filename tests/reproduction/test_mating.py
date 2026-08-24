"""Tests for mating compatibility and sexual-selection policies."""

from __future__ import annotations

import pytest

from evo_engine.genetics import CHOOSINESS, MATE_SEARCH_RANGE, MATING_SIGNAL
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    MutualMateSearchRange,
    MutualSignalCompatibility,
    MutualSignalMarginPreference,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def make_mating_state(
    *,
    first_range: int = 3,
    second_range: int = 3,
    first_choosiness: int = 5,
    second_choosiness: int = 5,
    first_signal: int = 8,
    second_signal: int = 8,
    first_x: int = 0,
    second_x: int = 2,
):
    """Return two organisms carrying the built-in mating traits."""
    architecture = make_integer_architecture(
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
    )
    state = make_state(
        width=10,
        height=10,
        genetic_architecture=architecture,
    )
    first = add_organism(
        state,
        trait_values={
            MATE_SEARCH_RANGE: first_range,
            CHOOSINESS: first_choosiness,
            MATING_SIGNAL: first_signal,
        },
        x=first_x,
        y=0,
    )
    second = add_organism(
        state,
        trait_values={
            MATE_SEARCH_RANGE: second_range,
            CHOOSINESS: second_choosiness,
            MATING_SIGNAL: second_signal,
        },
        x=second_x,
        y=0,
    )
    return state, first, second


def test_mutual_mate_search_range_requires_both_parents_to_reach_pair() -> None:
    """Test mutual discovery uses both organisms' search ranges."""
    state, first, second = make_mating_state(
        first_range=3,
        second_range=1,
        second_x=2,
    )
    policy = MutualMateSearchRange()

    assert not policy(first, second, state)


def test_mutual_mate_search_range_accepts_pair_inside_both_ranges() -> None:
    """Test a pair is discoverable when both expressed ranges cover distance."""
    state, first, second = make_mating_state(
        first_range=2,
        second_range=2,
        second_x=2,
    )

    assert MutualMateSearchRange()(first, second, state)


def test_mutual_mate_search_range_declares_trait_requirement() -> None:
    """Test mate-search range participates in engine trait preflight."""
    assert MutualMateSearchRange().required_traits == frozenset({MATE_SEARCH_RANGE})


@pytest.mark.parametrize(
    (
        "first_choosiness",
        "second_choosiness",
        "first_signal",
        "second_signal",
        "expected",
    ),
    [
        (5, 5, 8, 8, True),
        (9, 5, 8, 8, False),
        (5, 9, 8, 8, False),
        (8, 8, 8, 8, True),
    ],
)
def test_mutual_signal_compatibility_requires_two_way_acceptance(
    first_choosiness: int,
    second_choosiness: int,
    first_signal: int,
    second_signal: int,
    expected: bool,
) -> None:
    """Test each parent's signal must meet the other's choosiness threshold."""
    state, first, second = make_mating_state(
        first_choosiness=first_choosiness,
        second_choosiness=second_choosiness,
        first_signal=first_signal,
        second_signal=second_signal,
    )

    assert MutualSignalCompatibility()(first, second, state) is expected


def test_mutual_signal_compatibility_declares_both_traits() -> None:
    """Test choosiness and mating signal participate in trait preflight."""
    assert MutualSignalCompatibility().required_traits == frozenset(
        {CHOOSINESS, MATING_SIGNAL}
    )


def test_mutual_signal_margin_preference_is_symmetric() -> None:
    """Test interchangeable parent order does not change preference."""
    state, first, second = make_mating_state(
        first_choosiness=4,
        second_choosiness=6,
        first_signal=9,
        second_signal=8,
    )
    preference = MutualSignalMarginPreference()

    assert preference(first, second, state) == 7
    assert preference(second, first, state) == 7


def test_all_of_mating_compatibility_aggregates_nested_traits() -> None:
    """Test composed mating rules expose every genetic dependency."""
    policy = AllOfMatingCompatibility(
        compatibilities=(
            MutualMateSearchRange(),
            MutualSignalCompatibility(),
        )
    )

    assert policy.required_traits == frozenset(
        {MATE_SEARCH_RANGE, CHOOSINESS, MATING_SIGNAL}
    )


def test_all_of_mating_compatibility_requires_every_rule() -> None:
    """Test one failed mating rule rejects the candidate pair."""
    state, first, second = make_mating_state(
        first_range=1,
        second_range=3,
        second_x=2,
        first_signal=10,
        second_signal=10,
    )
    policy = AllOfMatingCompatibility(
        compatibilities=(
            MutualMateSearchRange(),
            MutualSignalCompatibility(),
        )
    )

    assert not policy(first, second, state)


def test_all_of_mating_compatibility_rejects_empty_composition() -> None:
    """Test mating compatibility cannot vacuously accept every pair."""
    with pytest.raises(ValueError):
        AllOfMatingCompatibility(compatibilities=())
