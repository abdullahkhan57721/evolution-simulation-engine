"""Tests for generic and biological operative characteristic boundaries."""

from __future__ import annotations

from evo_engine.characteristics import (
    DevelopmentalProfileCharacteristics,
    GeneticPhenotypeCharacteristics,
)
from evo_engine.growth import CharacteristicGrowthRate
from evo_engine.world import Organism
from tests.helpers import (
    developmental_profile,
    make_diploid_genome,
    make_integer_architecture,
    make_state,
)


def _organism_with_distinct_realized_growth() -> tuple[Organism, object]:
    architecture = make_integer_architecture("growth_rate")
    genome = make_diploid_genome(architecture, {"growth_rate": 2})
    genetic_phenotype = architecture.express(genome)
    organism = Organism(
        genome=genome,
        genetic_phenotype=genetic_phenotype,
        developmental_profile=developmental_profile(growth_rate=5),
    )
    return organism, architecture


def test_biological_sources_distinguish_genetic_and_realized_values() -> None:
    """Test source choice separates inherited expression from realized development."""
    organism, architecture = _organism_with_distinct_realized_growth()
    state = make_state(genetic_architecture=architecture)

    genetic_value = GeneticPhenotypeCharacteristics().value_for(
        organism,
        "growth_rate",
        context=state,
    )
    realized_value = DevelopmentalProfileCharacteristics().value_for(
        organism,
        "growth_rate",
        context=state,
    )

    assert genetic_value == 2
    assert realized_value == 5


def test_characteristic_growth_defaults_to_realized_development() -> None:
    """Test source-agnostic growth uses realized development by default."""
    organism, architecture = _organism_with_distinct_realized_growth()
    state = make_state(genetic_architecture=architecture)

    growth = CharacteristicGrowthRate().determine_body_mass_gain(
        organism,
        target_body_mass=10,
        simulation_state=state,
    )

    assert growth == 5


def test_characteristic_growth_can_explicitly_use_raw_genetic_expression() -> None:
    """Test scientific configurations may deliberately choose a genetic source."""
    organism, architecture = _organism_with_distinct_realized_growth()
    state = make_state(genetic_architecture=architecture)

    growth = CharacteristicGrowthRate(
        source=GeneticPhenotypeCharacteristics(),
    ).determine_body_mass_gain(
        organism,
        target_body_mass=10,
        simulation_state=state,
    )

    assert growth == 2
