"""Tests for organism-specific energy reserve expenditure policy."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    EnergyThresholdSource,
    KeepEnergyReserve,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_keep_energy_reserve_allows_exact_developmental_reserve() -> None:
    """Test positive expenditure may leave exactly the resolved reserve."""
    architecture = make_integer_architecture("reserve")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"reserve": 4},
        energy=10,
    )
    policy = KeepEnergyReserve(
        minimum_energy=DevelopmentalEnergyThreshold(trait_name="reserve")
    )

    assert policy.can_spend(
        organism,
        energy_cost=6,
        simulation_state=state,
    )
    assert policy.required_traits == frozenset({"reserve"})


def test_keep_energy_reserve_rejects_expenditure_below_reserve() -> None:
    """Test positive expenditure cannot cross the resolved reserve."""
    architecture = make_integer_architecture("reserve")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"reserve": 4},
        energy=9,
    )
    policy = KeepEnergyReserve(
        minimum_energy=DevelopmentalEnergyThreshold(trait_name="reserve")
    )

    assert not policy.can_spend(
        organism,
        energy_cost=6,
        simulation_state=state,
    )


def test_keep_energy_reserve_allows_zero_cost_below_reserve() -> None:
    """Test free actions remain available below the desired reserve."""
    architecture = make_integer_architecture("reserve")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"reserve": 10},
        energy=3,
    )
    policy = KeepEnergyReserve(
        minimum_energy=DevelopmentalEnergyThreshold(trait_name="reserve")
    )

    assert policy.can_spend(
        organism,
        energy_cost=0,
        simulation_state=state,
    )


def test_keep_energy_reserve_accepts_literal_threshold() -> None:
    """Test dynamic reserve policy also supports simple fixed configuration."""
    state = make_state()
    organism = add_organism(state, energy=10)
    policy = KeepEnergyReserve(minimum_energy=4)

    assert policy.can_spend(organism, energy_cost=6, simulation_state=state)
    assert policy.required_traits == frozenset()


def test_keep_energy_reserve_rejects_invalid_threshold_source() -> None:
    """Test reserve sources are validated when the policy is configured."""
    with pytest.raises(TypeError):
        KeepEnergyReserve(
            minimum_energy=cast(EnergyThresholdSource, object()),
        )
