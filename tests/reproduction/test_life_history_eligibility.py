"""Tests for life-history reproductive eligibility policies."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.energetics import DevelopmentalEnergyThreshold
from evo_engine.genetics import MATURITY_AGE, REPRODUCTION_ENERGY_THRESHOLD
from evo_engine.reproduction import (
    AllOfEligibility,
    DevelopmentalMaturityEligibility,
    MinimumAgeEligibility,
    MinimumEnergyEligibility,
    ReproductiveEligibility,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


@pytest.mark.parametrize(
    ("age", "minimum_age", "expected"),
    [
        (4, 5, False),
        (5, 5, True),
        (6, 5, True),
    ],
)
def test_minimum_age_eligibility(
    age: int,
    minimum_age: int,
    expected: bool,
) -> None:
    """Test fixed age eligibility at and around the maturity boundary."""
    state = make_state()
    organism = add_organism(state, age=age)

    assert (
        MinimumAgeEligibility(minimum_age=minimum_age).is_eligible(
            organism,
            simulation_state=state,
        )
        is expected
    )


@pytest.mark.parametrize("minimum_age", [-1, True, 1.0, "1"])
def test_minimum_age_eligibility_rejects_invalid_age(minimum_age: object) -> None:
    """Test fixed maturity ages are nonnegative integers."""
    with pytest.raises((TypeError, ValueError)):
        MinimumAgeEligibility(minimum_age=cast(int, minimum_age))


def test_developmental_maturity_eligibility_reads_target() -> None:
    """Test maturity may vary among organisms through developmental targets."""
    architecture = make_integer_architecture(MATURITY_AGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MATURITY_AGE: 7},
        age=6,
    )
    eligibility = DevelopmentalMaturityEligibility()

    assert eligibility.required_traits == frozenset({MATURITY_AGE})
    assert not eligibility.is_eligible(organism, simulation_state=state)

    organism.age = 7
    assert eligibility.is_eligible(organism, simulation_state=state)


def test_developmental_maturity_eligibility_rejects_negative_target() -> None:
    """Test developmental maturity ages cannot be negative."""
    architecture = make_integer_architecture(MATURITY_AGE)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={MATURITY_AGE: -1},
    )

    with pytest.raises(ValueError):
        DevelopmentalMaturityEligibility().is_eligible(
            organism,
            simulation_state=state,
        )


def test_minimum_energy_eligibility_supports_developmental_threshold() -> None:
    """Test reproductive energy thresholds may be organism-specific."""
    architecture = make_integer_architecture(REPRODUCTION_ENERGY_THRESHOLD)
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={REPRODUCTION_ENERGY_THRESHOLD: 12},
        energy=11,
    )
    eligibility = MinimumEnergyEligibility(
        minimum_energy=DevelopmentalEnergyThreshold(
            trait_name=REPRODUCTION_ENERGY_THRESHOLD,
        )
    )

    assert eligibility.required_traits == frozenset({REPRODUCTION_ENERGY_THRESHOLD})
    assert not eligibility.is_eligible(organism, simulation_state=state)

    organism.energy = 12
    assert eligibility.is_eligible(organism, simulation_state=state)


def test_all_of_eligibility_requires_every_nested_policy() -> None:
    """Test AND-composition short-circuits on a failed eligibility rule."""
    state = make_state()
    organism = add_organism(
        state,
        age=5,
        energy=9,
    )
    eligibility = AllOfEligibility(
        eligibilities=(
            MinimumAgeEligibility(minimum_age=5),
            MinimumEnergyEligibility(minimum_energy=10),
        )
    )

    assert not eligibility.is_eligible(organism, simulation_state=state)

    organism.energy = 10
    assert eligibility.is_eligible(organism, simulation_state=state)


def test_all_of_eligibility_collects_nested_trait_requirements() -> None:
    """Test composed eligibility exposes all nested trait dependencies."""
    eligibility = AllOfEligibility(
        eligibilities=(
            DevelopmentalMaturityEligibility(),
            MinimumEnergyEligibility(
                minimum_energy=DevelopmentalEnergyThreshold(
                    trait_name=REPRODUCTION_ENERGY_THRESHOLD,
                )
            ),
        )
    )

    assert eligibility.required_traits == frozenset(
        {MATURITY_AGE, REPRODUCTION_ENERGY_THRESHOLD}
    )


def test_all_of_eligibility_rejects_empty_composition() -> None:
    """Test empty AND-compositions use AlwaysEligible instead."""
    with pytest.raises(ValueError):
        AllOfEligibility(eligibilities=())


def test_all_of_eligibility_rejects_invalid_nested_policy() -> None:
    """Test every nested item must provide reproductive eligibility behavior."""
    with pytest.raises(TypeError):
        AllOfEligibility(
            eligibilities=cast(tuple[ReproductiveEligibility, ...], (object(),))
        )


def test_all_of_eligibility_rejects_non_boolean_nested_decision() -> None:
    """Test composed eligibility validates nested return contracts."""

    class InvalidEligibility:
        def is_eligible(
            self,
            organism,
            *,
            simulation_state,
        ):
            return 1

    state = make_state()
    organism = add_organism(state)
    eligibility = AllOfEligibility(
        eligibilities=(cast(ReproductiveEligibility, InvalidEligibility()),)
    )

    with pytest.raises(TypeError, match="must return a Boolean"):
        eligibility.is_eligible(
            organism,
            simulation_state=state,
        )
