"""Tests for trait-driven metabolic and locomotion power-law costs."""

from __future__ import annotations

from evo_engine.energetics import (
    GeneticPhenotypeCoefficient,
    PowerLawLocomotionCost,
    PowerLawMetabolicCost,
)
from evo_engine.genetics import (
    LOCOMOTION_COST_COEFFICIENT,
    METABOLIC_COST_COEFFICIENT,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_metabolic_cost_varies_with_genetic_coefficient() -> None:
    """Test equal-mass organisms can have different basal expenditures."""
    architecture = make_integer_architecture(METABOLIC_COST_COEFFICIENT)
    state = make_state(
        genetic_architecture=architecture,
    )
    efficient = add_organism(
        state,
        trait_values={METABOLIC_COST_COEFFICIENT: 25},
        body_mass=4,
    )
    costly = add_organism(
        state,
        trait_values={METABOLIC_COST_COEFFICIENT: 50},
        body_mass=4,
    )
    model = PowerLawMetabolicCost(
        coefficient=GeneticPhenotypeCoefficient(
            trait_name=METABOLIC_COST_COEFFICIENT,
        ),
        mass_exponent=1.0,
    )

    assert model.calculate_cost(efficient, state) == 1
    assert model.calculate_cost(costly, state) == 2
    assert model.required_traits == frozenset({METABOLIC_COST_COEFFICIENT})


def test_locomotion_cost_varies_with_genetic_coefficient() -> None:
    """Test the same displacement can cost genetically different amounts."""
    architecture = make_integer_architecture(LOCOMOTION_COST_COEFFICIENT)
    state = make_state(
        genetic_architecture=architecture,
    )
    efficient = add_organism(
        state,
        trait_values={LOCOMOTION_COST_COEFFICIENT: 50},
        body_mass=4,
    )
    costly = add_organism(
        state,
        trait_values={LOCOMOTION_COST_COEFFICIENT: 100},
        body_mass=4,
    )
    model = PowerLawLocomotionCost(
        coefficient=GeneticPhenotypeCoefficient(
            trait_name=LOCOMOTION_COST_COEFFICIENT,
        ),
        mass_exponent=0.0,
        distance_exponent=1.0,
    )

    assert (
        model.calculate_cost(
            efficient,
            dx=2,
            dy=0,
            simulation_state=state,
        )
        == 1
    )
    assert (
        model.calculate_cost(
            costly,
            dx=2,
            dy=0,
            simulation_state=state,
        )
        == 2
    )
    assert model.required_traits == frozenset({LOCOMOTION_COST_COEFFICIENT})
