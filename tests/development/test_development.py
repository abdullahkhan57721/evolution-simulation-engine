"""Tests for developmental realization models."""

from __future__ import annotations

import random

import pytest

from evo_engine.development import (
    DeterministicDevelopment,
    DevelopmentalProfile,
    GaussianIntegerDevelopment,
    IndependentDevelopment,
    realize_developmental_profile,
)
from evo_engine.genetics import ADULT_BODY_MASS, MAX_SPEED, GeneticPhenotype


class _StaticDevelopmentModel:
    """Return a preconfigured developmental profile for contract tests."""

    required_traits = frozenset()

    def __init__(self, profile: DevelopmentalProfile) -> None:
        self.profile = profile

    def develop(
        self,
        genetic_phenotype: GeneticPhenotype,
        *,
        rng: random.Random,
        simulation_state=None,
    ) -> DevelopmentalProfile:
        """Return the preconfigured profile regardless of trait values."""
        return self.profile


def test_developmental_profile_is_mapping() -> None:
    """Test named target lookup and integer access."""
    profile = DevelopmentalProfile(
        target_values=(
            (ADULT_BODY_MASS, 20),
            (MAX_SPEED, 3),
        ),
    )

    assert profile[ADULT_BODY_MASS] == 20
    assert profile.int_value(MAX_SPEED) == 3
    assert tuple(profile) == (
        ADULT_BODY_MASS,
        MAX_SPEED,
    )


def test_developmental_profile_rejects_duplicate_names() -> None:
    """Test each developmental target name is unique."""
    with pytest.raises(ValueError):
        DevelopmentalProfile(
            target_values=(
                (ADULT_BODY_MASS, 20),
                (ADULT_BODY_MASS, 21),
            ),
        )


def test_deterministic_development_copies_genetic_phenotype() -> None:
    """Test the null developmental model preserves genetic values."""
    genetic_phenotype = GeneticPhenotype(
        trait_values=(
            (ADULT_BODY_MASS, 20),
            (MAX_SPEED, 3),
        ),
    )

    profile = DeterministicDevelopment().develop(
        genetic_phenotype,
        rng=random.Random(1),
    )

    assert profile.target_values == genetic_phenotype.trait_values


def test_realize_developmental_profile_preserves_complete_ordered_trait_set() -> None:
    """Test development may change values while preserving trait identity/order."""
    genetic_phenotype = GeneticPhenotype(
        trait_values=(
            (ADULT_BODY_MASS, 20),
            (MAX_SPEED, 3),
        ),
    )
    expected = DevelopmentalProfile(
        target_values=(
            (ADULT_BODY_MASS, 23),
            (MAX_SPEED, 4),
        ),
    )

    result = realize_developmental_profile(
        _StaticDevelopmentModel(expected),
        genetic_phenotype,
        rng=random.Random(1),
    )

    assert result is expected


@pytest.mark.parametrize(
    "target_values",
    [
        ((ADULT_BODY_MASS, 23),),
        ((ADULT_BODY_MASS, 23), (MAX_SPEED, 4), ("extra_trait", 1)),
        ((MAX_SPEED, 4), (ADULT_BODY_MASS, 23)),
    ],
)
def test_realize_developmental_profile_rejects_changed_trait_set_or_order(
    target_values: tuple[tuple[str, int], ...],
) -> None:
    """Test development cannot add, remove, or reorder genetic traits."""
    genetic_phenotype = GeneticPhenotype(
        trait_values=(
            (ADULT_BODY_MASS, 20),
            (MAX_SPEED, 3),
        ),
    )
    model = _StaticDevelopmentModel(
        DevelopmentalProfile(target_values=target_values),
    )

    with pytest.raises(ValueError, match="complete ordered trait set"):
        realize_developmental_profile(
            model,
            genetic_phenotype,
            rng=random.Random(1),
        )


def test_gaussian_integer_development_is_seed_reproducible() -> None:
    """Test Gaussian developmental variation uses the supplied RNG."""
    model = GaussianIntegerDevelopment(
        standard_deviation=2,
        minimum=1,
    )

    assert (
        model.develop(
            20,
            rng=random.Random(1),
        )
        == 23
    )
    assert (
        model.develop(
            20,
            rng=random.Random(1),
        )
        == 23
    )


def test_gaussian_integer_development_clamps_bounds() -> None:
    """Test developmental noise cannot violate configured target bounds."""
    model = GaussianIntegerDevelopment(
        standard_deviation=100,
        minimum=1,
        maximum=10,
    )

    result = model.develop(
        5,
        rng=random.Random(2),
    )

    assert 1 <= result <= 10


def test_independent_development_varies_only_configured_traits() -> None:
    """Test unconfigured genetic phenotype traits remain deterministic."""
    genetic_phenotype = GeneticPhenotype(
        trait_values=(
            (ADULT_BODY_MASS, 20),
            (MAX_SPEED, 3),
        ),
    )
    model = IndependentDevelopment(
        trait_models=(
            (
                ADULT_BODY_MASS,
                GaussianIntegerDevelopment(
                    standard_deviation=2,
                    minimum=1,
                ),
            ),
        ),
    )

    profile = model.develop(
        genetic_phenotype,
        rng=random.Random(1),
    )

    assert profile[ADULT_BODY_MASS] == 23
    assert profile[MAX_SPEED] == 3
    assert model.required_traits == frozenset({ADULT_BODY_MASS})


def test_independent_development_rejects_missing_configured_trait() -> None:
    """Test misspelled developmental trait configuration fails early."""
    model = IndependentDevelopment(
        trait_models=(
            (
                ADULT_BODY_MASS,
                GaussianIntegerDevelopment(
                    standard_deviation=1,
                ),
            ),
        ),
    )

    with pytest.raises(KeyError):
        model.develop(
            GeneticPhenotype(trait_values=()),
            rng=random.Random(1),
        )
