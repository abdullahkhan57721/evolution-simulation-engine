"""Tests for general energy-expenditure policies."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.energetics import (
    EnergyExpenditurePolicy,
    KeepFixedReserve,
    SpendToZero,
    energy_expenditure_is_allowed,
)
from tests.helpers import add_organism, make_state


def test_spend_to_zero_allows_exact_expenditure() -> None:
    """Test the default policy permits spending the final energy unit."""
    state = make_state()
    organism = add_organism(state, energy=5)

    assert energy_expenditure_is_allowed(
        SpendToZero(),
        organism,
        energy_cost=5,
        simulation_state=state,
    )


def test_spend_to_zero_rejects_cost_above_current_energy() -> None:
    """Test the default policy still requires full affordability."""
    state = make_state()
    organism = add_organism(state, energy=5)

    assert not energy_expenditure_is_allowed(
        SpendToZero(),
        organism,
        energy_cost=6,
        simulation_state=state,
    )


def test_keep_fixed_reserve_allows_exact_reserve_boundary() -> None:
    """Test payment may leave exactly the configured reserve."""
    state = make_state()
    organism = add_organism(state, energy=8)

    assert energy_expenditure_is_allowed(
        KeepFixedReserve(minimum_energy=3),
        organism,
        energy_cost=5,
        simulation_state=state,
    )


def test_keep_fixed_reserve_rejects_payment_below_reserve() -> None:
    """Test positive expenditures may not cross the configured reserve."""
    state = make_state()
    organism = add_organism(state, energy=7)

    assert not energy_expenditure_is_allowed(
        KeepFixedReserve(minimum_energy=3),
        organism,
        energy_cost=5,
        simulation_state=state,
    )


def test_keep_fixed_reserve_allows_zero_cost_below_reserve() -> None:
    """Test free actions do not get suppressed by an existing reserve deficit."""
    state = make_state()
    organism = add_organism(state, energy=2)

    assert energy_expenditure_is_allowed(
        KeepFixedReserve(minimum_energy=5),
        organism,
        energy_cost=0,
        simulation_state=state,
    )


@pytest.mark.parametrize(
    "minimum_energy",
    [
        -1,
        1.5,
        True,
        "1",
        None,
    ],
)
def test_keep_fixed_reserve_rejects_invalid_minimum_energy(
    minimum_energy: object,
) -> None:
    """Test fixed reserves must be non-negative integers."""
    with pytest.raises((TypeError, ValueError)):
        KeepFixedReserve(
            minimum_energy=minimum_energy,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "energy_cost",
    [
        -1,
        1.5,
        True,
        "1",
        None,
    ],
)
def test_expenditure_boundary_rejects_invalid_energy_cost(
    energy_cost: object,
) -> None:
    """Test the public expenditure boundary validates proposed costs."""
    state = make_state()
    organism = add_organism(state)

    with pytest.raises((TypeError, ValueError)):
        energy_expenditure_is_allowed(
            SpendToZero(),
            organism,
            energy_cost=energy_cost,  # type: ignore[arg-type]
            simulation_state=state,
        )


def test_expenditure_boundary_rejects_non_boolean_policy_output() -> None:
    """Test custom expenditure policies must return a Boolean."""

    class InvalidPolicy:
        def can_spend(
            self,
            organism,
            *,
            energy_cost,
            simulation_state,
        ):
            return 1

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(TypeError, match="must return a Boolean"):
        energy_expenditure_is_allowed(
            cast(EnergyExpenditurePolicy, InvalidPolicy()),
            organism,
            energy_cost=1,
            simulation_state=state,
        )


def test_expenditure_policy_protocol_accepts_structural_implementation() -> None:
    """Test custom policies need not inherit from engine classes."""

    class CustomPolicy:
        def can_spend(
            self,
            organism,
            *,
            energy_cost,
            simulation_state,
        ) -> bool:
            return True

    assert isinstance(CustomPolicy(), EnergyExpenditurePolicy)
