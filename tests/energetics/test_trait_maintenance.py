"""Tests for explicit physiological maintenance tradeoffs."""

from __future__ import annotations

import pytest

from evo_engine.energetics import (
    AdditiveMetabolicCost,
    FixedMetabolicCost,
    LinearTraitMaintenanceCost,
    TraitMaintenanceTerm,
)
from evo_engine.world import Organism
from tests.helpers import (
    developmental_profile,
    genetic_phenotype,
    make_empty_genome,
    make_state,
)


def _organism(*, genetic_value: int, realized_value: int) -> Organism:
    return Organism(
        energy=100,
        body_mass=1,
        genome=make_empty_genome(),
        genetic_phenotype=genetic_phenotype(performance=genetic_value),
        developmental_profile=developmental_profile(performance=realized_value),
    )


def test_trait_maintenance_uses_realized_developmental_value() -> None:
    """Test physiological cost follows realized rather than raw genetic value."""
    model = LinearTraitMaintenanceCost(
        terms=(
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=100,
            ),
        )
    )
    organism = _organism(genetic_value=2, realized_value=5)

    assert model.calculate_cost(organism, make_state()) == 5


def test_trait_maintenance_sums_fractional_burdens_before_rounding() -> None:
    """Test modest physiological burdens combine before integer rounding."""
    model = LinearTraitMaintenanceCost(
        terms=(
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=10,
            ),
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=10,
            ),
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=10,
            ),
        )
    )
    organism = _organism(genetic_value=2, realized_value=2)

    assert model.calculate_cost(organism, make_state()) == 1


def test_repeated_trait_terms_support_increasing_marginal_cost() -> None:
    """Test repeated terms create piecewise-linear physiological tradeoffs."""
    model = LinearTraitMaintenanceCost(
        terms=(
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=50,
            ),
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=50,
                baseline=4,
            ),
        )
    )
    organism = _organism(genetic_value=6, realized_value=6)

    assert model.calculate_cost(organism, make_state()) == 4


def test_additive_metabolic_cost_combines_basal_and_trait_maintenance() -> None:
    """Test basal metabolism composes with explicit physiological maintenance."""
    maintenance = LinearTraitMaintenanceCost(
        terms=(
            TraitMaintenanceTerm(
                trait_name="performance",
                cost_numerator=100,
            ),
        )
    )
    model = AdditiveMetabolicCost(
        cost_models=(FixedMetabolicCost(amount=2), maintenance),
    )
    organism = _organism(genetic_value=3, realized_value=3)

    assert model.calculate_cost(organism, make_state()) == 5
    assert model.required_traits == frozenset({"performance"})


def test_trait_maintenance_requires_at_least_one_term() -> None:
    """Test empty maintenance configuration is rejected."""
    with pytest.raises(ValueError, match="terms must not be empty"):
        LinearTraitMaintenanceCost(terms=())


def test_additive_metabolic_cost_requires_at_least_one_component() -> None:
    """Test empty metabolic composition is rejected."""
    with pytest.raises(ValueError, match="cost_models must not be empty"):
        AdditiveMetabolicCost(cost_models=())
