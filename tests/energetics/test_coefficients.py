"""Tests for fixed and organism-specific energetic coefficient sources."""

from __future__ import annotations

import math

import pytest

from evo_engine.energetics import (
    CoefficientModel,
    GeneticPhenotypeCoefficient,
    determine_coefficient,
    validate_coefficient_source,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_genetic_phenotype_coefficient_scales_integer_trait() -> None:
    """Test integer genetic coefficients can represent fractional values."""
    architecture = make_integer_architecture("cost_coefficient")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"cost_coefficient": 30},
    )
    model = GeneticPhenotypeCoefficient(
        trait_name="cost_coefficient",
        denominator=100,
    )

    assert (
        determine_coefficient(
            model,
            organism,
            simulation_state=state,
        )
        == 0.30
    )
    assert model.required_traits == frozenset({"cost_coefficient"})


def test_determine_coefficient_preserves_fixed_numeric_source() -> None:
    """Test existing fixed-number coefficient usage remains supported."""
    state = make_state()
    organism = add_organism(state)

    assert (
        determine_coefficient(
            0.75,
            organism,
            simulation_state=state,
        )
        == 0.75
    )


@pytest.mark.parametrize(
    "value",
    [
        -0.1,
        math.inf,
        -math.inf,
        math.nan,
        True,
        "0.5",
        None,
    ],
)
def test_validate_coefficient_source_rejects_invalid_fixed_values(
    value: object,
) -> None:
    """Test fixed coefficients must be finite nonnegative numbers."""
    with pytest.raises((TypeError, ValueError)):
        validate_coefficient_source(value)


@pytest.mark.parametrize(
    ("trait_name", "denominator"),
    [
        ("", 100),
        (" ", 100),
        ("cost", 0),
        ("cost", -1),
    ],
)
def test_genetic_phenotype_coefficient_rejects_invalid_configuration(
    trait_name: str,
    denominator: int,
) -> None:
    """Test coefficient trait names and scale denominators are valid."""
    with pytest.raises((TypeError, ValueError)):
        GeneticPhenotypeCoefficient(
            trait_name=trait_name,
            denominator=denominator,
        )


def test_coefficient_model_protocol_accepts_structural_implementation() -> None:
    """Test custom coefficient models need not inherit from engine classes."""

    class CustomCoefficient:
        def determine_coefficient(
            self,
            organism,
            *,
            simulation_state,
        ) -> float:
            return 0.5

    assert isinstance(CustomCoefficient(), CoefficientModel)


def test_determine_coefficient_validates_custom_model_output() -> None:
    """Test coefficient model outputs retain finite nonnegative contracts."""

    class InvalidCoefficient:
        def determine_coefficient(
            self,
            organism,
            *,
            simulation_state,
        ) -> float:
            return -0.1

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(ValueError):
        determine_coefficient(
            InvalidCoefficient(),
            organism,
            simulation_state=state,
        )
