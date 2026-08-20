"""Tests for growth energy-cost models."""

from __future__ import annotations

import math

import pytest

from evo_engine.energetics import LinearGrowthCost
from tests.helpers import add_organism, make_state


def test_linear_growth_cost_scales_with_body_mass_gain() -> None:
    """Test growth cost is proportional to actual body-mass gain."""
    state = make_state()
    organism = add_organism(state)

    cost = LinearGrowthCost(
        energy_per_body_mass_unit=2,
    ).calculate_cost(
        organism,
        body_mass_gain=3,
        simulation_state=state,
    )

    assert cost == 6


def test_linear_growth_cost_uses_half_up_rounding() -> None:
    """Test half-integer energetic growth costs round upward."""
    state = make_state()
    organism = add_organism(state)

    cost = LinearGrowthCost(
        energy_per_body_mass_unit=0.5,
    ).calculate_cost(
        organism,
        body_mass_gain=1,
        simulation_state=state,
    )

    assert cost == 1


def test_linear_growth_cost_applies_minimum_to_nonzero_growth() -> None:
    """Test small positive growth can retain a configured energy floor."""
    state = make_state()
    organism = add_organism(state)

    cost = LinearGrowthCost(
        energy_per_body_mass_unit=0.1,
        minimum_nonzero_cost=2,
    ).calculate_cost(
        organism,
        body_mass_gain=1,
        simulation_state=state,
    )

    assert cost == 2


def test_linear_growth_cost_never_charges_for_zero_growth() -> None:
    """Test minimum nonzero cost does not create a zero-growth charge."""
    state = make_state()
    organism = add_organism(state)

    cost = LinearGrowthCost(
        energy_per_body_mass_unit=10,
        minimum_nonzero_cost=4,
    ).calculate_cost(
        organism,
        body_mass_gain=0,
        simulation_state=state,
    )

    assert cost == 0


@pytest.mark.parametrize(
    "value",
    [
        -1.0,
        math.inf,
        -math.inf,
        math.nan,
        True,
        "1",
    ],
)
def test_linear_growth_cost_rejects_invalid_coefficient(value: object) -> None:
    """Test growth-energy coefficient must be finite and nonnegative."""
    with pytest.raises((TypeError, ValueError)):
        LinearGrowthCost(
            energy_per_body_mass_unit=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "value",
    [
        -1,
        1.5,
        True,
        "1",
    ],
)
def test_linear_growth_cost_rejects_invalid_body_mass_gain(value: object) -> None:
    """Test priced body-mass gain must be a nonnegative integer."""
    state = make_state()
    organism = add_organism(state)
    model = LinearGrowthCost(
        energy_per_body_mass_unit=1,
    )

    with pytest.raises((TypeError, ValueError)):
        model.calculate_cost(
            organism,
            body_mass_gain=value,  # type: ignore[arg-type]
            simulation_state=state,
        )
