"""Tests for mating policy integration with pairwise parent selection."""

from __future__ import annotations

from evo_engine.genetics import CHOOSINESS, MATE_SEARCH_RANGE, MATING_SIGNAL
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    MutualMateSearchRange,
    MutualSignalCompatibility,
    MutualSignalMarginPreference,
    PairwiseMating,
)
from evo_engine.spatial.neighborhoods import SameCell


def test_pairwise_mating_aggregates_structured_policy_trait_requirements() -> None:
    """Test mating policy dependencies propagate into reproduction preflight."""
    policy = PairwiseMating(
        neighborhood=SameCell(),
        can_mate=AllOfMatingCompatibility(
            compatibilities=(
                MutualMateSearchRange(),
                MutualSignalCompatibility(),
            )
        ),
        preference_function=MutualSignalMarginPreference(),
    )

    assert policy.required_traits == frozenset(
        {MATE_SEARCH_RANGE, CHOOSINESS, MATING_SIGNAL}
    )


def test_pairwise_mating_preserves_explicit_opaque_callback_requirements() -> None:
    """Test manual dependencies still compose with structured policy metadata."""
    policy = PairwiseMating(
        neighborhood=SameCell(),
        can_mate=MutualMateSearchRange(),
        required_traits=frozenset({"custom_compatibility_trait"}),
    )

    assert policy.required_traits == frozenset(
        {MATE_SEARCH_RANGE, "custom_compatibility_trait"}
    )
