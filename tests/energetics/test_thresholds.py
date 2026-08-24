"""Tests for reusable energy-threshold models."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.energetics import (
    DevelopmentalEnergyThreshold,
    EnergyThresholdModel,
    FixedEnergyThreshold,
    determine_energy_threshold,
    validate_energy_threshold_source,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_fixed_energy_threshold_returns_configured_value() -> None:
    """Test fixed threshold models return the configured threshold."""
    state = make_state()
    organism = add_organism(state)

    assert (
        FixedEnergyThreshold(threshold=7).determine_threshold(
            organism,
            simulation_state=state,
        )
        == 7
    )


@pytest.mark.parametrize(
    "threshold",
    [-1, True, 1.0, "1"],
)
def test_fixed_energy_threshold_rejects_invalid_values(threshold: object) -> None:
    """Test fixed thresholds are nonnegative integers."""
    with pytest.raises((TypeError, ValueError)):
        FixedEnergyThreshold(threshold=cast(int, threshold))


def test_developmental_energy_threshold_reads_individual_target() -> None:
    """Test developmental threshold models use organism-specific targets."""
    architecture = make_integer_architecture("reserve")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"reserve": 12},
    )
    model = DevelopmentalEnergyThreshold(trait_name="reserve")

    assert model.required_traits == frozenset({"reserve"})
    assert model.determine_threshold(organism, simulation_state=state) == 12


def test_developmental_energy_threshold_rejects_negative_target() -> None:
    """Test developmental energy thresholds cannot be negative."""
    architecture = make_integer_architecture("reserve")
    state = make_state(genetic_architecture=architecture)
    organism = add_organism(
        state,
        trait_values={"reserve": -1},
    )
    model = DevelopmentalEnergyThreshold(trait_name="reserve")

    with pytest.raises(ValueError):
        model.determine_threshold(
            organism,
            simulation_state=state,
        )


@pytest.mark.parametrize("trait_name", ["", " "])
def test_developmental_energy_threshold_rejects_blank_trait_name(
    trait_name: str,
) -> None:
    """Test developmental threshold trait names are nonblank."""
    with pytest.raises(ValueError):
        DevelopmentalEnergyThreshold(trait_name=trait_name)


def test_energy_threshold_protocol_accepts_structural_implementation() -> None:
    """Test custom threshold models need not inherit engine classes."""

    class CustomThreshold:
        def determine_threshold(
            self,
            organism,
            *,
            simulation_state,
        ) -> int:
            return 3

    assert isinstance(CustomThreshold(), EnergyThresholdModel)


def test_determine_energy_threshold_accepts_literal_integer() -> None:
    """Test simple configurations may continue using literal thresholds."""
    state = make_state()
    organism = add_organism(state)

    assert determine_energy_threshold(4, organism, simulation_state=state) == 4


def test_determine_energy_threshold_validates_model_return_value() -> None:
    """Test threshold-model return contracts are enforced at the boundary."""

    class InvalidThreshold:
        def determine_threshold(
            self,
            organism,
            *,
            simulation_state,
        ):
            return -1

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_energy_threshold(
            cast(EnergyThresholdModel, InvalidThreshold()),
            organism,
            simulation_state=state,
        )


def test_validate_energy_threshold_source_rejects_invalid_object() -> None:
    """Test threshold sources must be integers or threshold models."""
    with pytest.raises(TypeError):
        validate_energy_threshold_source(object())
