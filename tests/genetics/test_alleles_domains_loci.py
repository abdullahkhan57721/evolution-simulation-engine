"""Tests for allele, domain, and locus primitives."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Allele,
    ChoiceAlleleDomain,
    GaussianIntegerMutation,
    IntegerAlleleDomain,
    Locus,
    NoMutation,
    UniformIntegerMutation,
)


def test_allele_requires_nonblank_locus_name() -> None:
    """Test allele identity validation."""
    with pytest.raises(ValueError):
        Allele(
            locus_name="   ",
            value=1,
        )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-3, 0),
        (0, 0),
        (5, 5),
        (12, 10),
    ],
)
def test_integer_domain_constrain_clamps_bounds(
    value: int,
    expected: int,
) -> None:
    """Test integer allele candidates clamp to configured bounds."""
    domain = IntegerAlleleDomain(
        minimum=0,
        maximum=10,
    )

    assert domain.constrain(value) == expected


@pytest.mark.parametrize("value", [-1, 11])
def test_integer_domain_validate_rejects_out_of_range(value: int) -> None:
    """Test integer domains reject stored values outside bounds."""
    domain = IntegerAlleleDomain(
        minimum=0,
        maximum=10,
    )

    with pytest.raises(ValueError):
        domain.validate(value)


def test_integer_domain_rejects_inverted_bounds() -> None:
    """Test that domain boundaries form a valid interval."""
    with pytest.raises(ValueError):
        IntegerAlleleDomain(
            minimum=5,
            maximum=4,
        )


def test_choice_domain_accepts_only_configured_values() -> None:
    """Test finite categorical allele domains."""
    domain = ChoiceAlleleDomain(
        values=("A", "a"),
    )

    domain.validate("A")

    with pytest.raises(ValueError):
        domain.validate("B")


def test_choice_domain_rejects_duplicate_values() -> None:
    """Test unambiguous finite allele domains."""
    with pytest.raises(ValueError):
        ChoiceAlleleDomain(
            values=("A", "A"),
        )


def test_locus_creates_valid_self_identifying_allele() -> None:
    """Test locus-owned allele creation."""
    locus = Locus(
        name="adult_body_mass",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(minimum=1),
        mutation=NoMutation(),
    )

    allele = locus.create_allele(4)

    assert allele == Allele(
        locus_name="adult_body_mass",
        value=4,
    )


def test_locus_rejects_allele_from_other_locus() -> None:
    """Test that a locus cannot validate another locus's allele."""
    locus = Locus(
        name="a",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError):
        locus.validate_allele(
            Allele(
                locus_name="b",
                value=1,
            )
        )


def test_locus_mutation_constrains_candidate_to_domain() -> None:
    """Test locus mutation guarantees a legal resulting allele."""
    locus = Locus(
        name="size",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(
            minimum=1,
            maximum=1,
        ),
        mutation=UniformIntegerMutation(
            probability_ppm=1_000_000,
            max_change=10,
        ),
    )

    mutated = locus.mutate(
        locus.create_allele(1),
        rng=random.Random(2),
    )

    assert mutated.value == 1


def test_no_mutation_returns_value_unchanged() -> None:
    """Test the explicit no-mutation policy."""
    assert (
        NoMutation[int]().mutate(
            7,
            rng=random.Random(1),
        )
        == 7
    )


def test_uniform_integer_mutation_probability_zero_is_identity() -> None:
    """Test zero mutation probability."""
    policy = UniformIntegerMutation(
        probability_ppm=0,
        max_change=3,
    )

    assert (
        policy.mutate(
            10,
            rng=random.Random(1),
        )
        == 10
    )


def test_uniform_integer_mutation_with_probability_one_changes_value() -> None:
    """Test successful uniform mutation always has nonzero magnitude."""
    policy = UniformIntegerMutation(
        probability_ppm=1_000_000,
        max_change=3,
    )

    assert (
        policy.mutate(
            10,
            rng=random.Random(1),
        )
        != 10
    )


def test_gaussian_mutation_zero_standard_deviation_is_identity() -> None:
    """Test a degenerate Gaussian mutation distribution."""
    policy = GaussianIntegerMutation(
        probability_ppm=1_000_000,
        standard_deviation=0,
    )

    assert (
        policy.mutate(
            10,
            rng=random.Random(1),
        )
        == 10
    )


@pytest.mark.parametrize(
    ("probability_ppm", "standard_deviation"),
    [
        (-1, 1),
        (1_000_001, 1),
        (10, -1),
    ],
)
def test_gaussian_mutation_rejects_invalid_configuration(
    probability_ppm: int,
    standard_deviation: int,
) -> None:
    """Test Gaussian mutation configuration validation."""
    with pytest.raises(ValueError):
        GaussianIntegerMutation(
            probability_ppm=probability_ppm,
            standard_deviation=standard_deviation,
        )
