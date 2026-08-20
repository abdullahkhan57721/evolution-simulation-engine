"""Tests for metabolic and locomotion energy-cost models."""

from __future__ import annotations

import math

import pytest

from evo_engine.energetics import (
    FixedLocomotionCost,
    FixedMetabolicCost,
    PowerLawLocomotionCost,
    PowerLawMetabolicCost,
)
from tests.helpers import (
    add_organism,
    make_integer_architecture,
    make_state,
)


def test_fixed_metabolic_cost_returns_configured_amount() -> None:
    """Test fixed basal expenditure."""
    state = make_state()
    organism = add_organism(state)

    assert (
        FixedMetabolicCost(
            amount=7,
        ).calculate_cost(
            organism,
            state,
        )
        == 7
    )


def test_power_law_metabolic_cost_uses_current_body_mass() -> None:
    """Test configurable allometric-style scaling uses mutable current mass."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 16},
    )

    cost = PowerLawMetabolicCost(
        coefficient=2.0,
        mass_exponent=0.75,
    ).calculate_cost(
        organism,
        state,
    )

    assert cost == 16


def test_power_law_metabolic_cost_applies_minimum_after_rounding() -> None:
    """Test small positive costs can retain a configured floor."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 1},
    )

    cost = PowerLawMetabolicCost(
        coefficient=0.1,
        mass_exponent=1.0,
        minimum_cost=1,
    ).calculate_cost(
        organism,
        state,
    )

    assert cost == 1


def test_fixed_locomotion_cost_is_zero_when_stationary() -> None:
    """Test locomotion does not duplicate basal expenditure."""
    state = make_state()
    organism = add_organism(state)

    cost = FixedLocomotionCost(
        amount=5,
    ).calculate_cost(
        organism,
        dx=0,
        dy=0,
        simulation_state=state,
    )

    assert cost == 0


def test_power_law_locomotion_cost_uses_current_mass_and_euclidean_distance() -> None:
    """Test configurable mass-distance locomotion scaling."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 8},
    )

    cost = PowerLawLocomotionCost(
        coefficient=1.0,
        mass_exponent=2 / 3,
        distance_exponent=1.0,
    ).calculate_cost(
        organism,
        dx=3,
        dy=4,
        simulation_state=state,
    )

    assert cost == 20


def test_organism_rejects_nonpositive_current_body_mass() -> None:
    """Test current physical body mass retains a positive invariant."""
    state = make_state()

    with pytest.raises(ValueError):
        add_organism(
            state,
            body_mass=0,
        )


@pytest.mark.parametrize(
    "value",
    [
        math.inf,
        -math.inf,
        math.nan,
    ],
)
def test_power_law_models_reject_nonfinite_configuration(value: float) -> None:
    """Test non-finite scaling parameters are rejected."""
    with pytest.raises(ValueError):
        PowerLawMetabolicCost(
            coefficient=value,
            mass_exponent=1.0,
        )


def test_power_law_cost_uses_current_mass_not_adult_mass_target() -> None:
    """Test energetics responds to mutable physical mass during development."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"adult_body_mass": 20},
        body_mass=4,
    )

    cost = PowerLawMetabolicCost(
        coefficient=1.0,
        mass_exponent=1.0,
    ).calculate_cost(
        organism,
        state,
    )

    assert cost == 4
