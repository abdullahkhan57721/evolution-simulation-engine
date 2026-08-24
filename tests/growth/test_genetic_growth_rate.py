"""Tests for trait-driven organism growth rates."""

from __future__ import annotations

import pytest

from evo_engine.genetics import GROWTH_RATE
from evo_engine.growth import GeneticPhenotypeGrowthRate
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_genetic_growth_rate_reads_expressed_trait() -> None:
    """Test potential growth can vary between genetically different organisms."""
    architecture = make_integer_architecture(GROWTH_RATE)
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={GROWTH_RATE: 3},
    )
    model = GeneticPhenotypeGrowthRate()

    assert (
        model.determine_body_mass_gain(
            organism,
            target_body_mass=10,
            simulation_state=state,
        )
        == 3
    )
    assert model.required_traits == frozenset({GROWTH_RATE})


def test_genetic_growth_rate_supports_custom_trait_name() -> None:
    """Test simulations may reuse the model with custom genetic vocabularies."""
    architecture = make_integer_architecture("juvenile_growth")
    state = make_state(
        genetic_architecture=architecture,
    )
    organism = add_organism(
        state,
        trait_values={"juvenile_growth": 2},
    )
    model = GeneticPhenotypeGrowthRate(
        trait_name="juvenile_growth",
    )

    assert (
        model.determine_body_mass_gain(
            organism,
            target_body_mass=10,
            simulation_state=state,
        )
        == 2
    )


@pytest.mark.parametrize(
    "trait_name",
    [
        "",
        " ",
    ],
)
def test_genetic_growth_rate_rejects_blank_trait_name(trait_name: str) -> None:
    """Test growth-rate trait dependency names must be usable."""
    with pytest.raises(ValueError):
        GeneticPhenotypeGrowthRate(
            trait_name=trait_name,
        )
