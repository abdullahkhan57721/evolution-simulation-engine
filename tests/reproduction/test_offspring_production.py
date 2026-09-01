"""Tests for biological offspring production after state propagation."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import GeneticArchitecture, Genome
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    BiologicalOffspringProduction,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    OffspringProductionContext,
    SingleParent,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


class PropagationOnlyInheritance:
    """Inheritance adapter whose legacy method must not drive reproduction."""

    required_traits = frozenset()

    @property
    def parent_count(self) -> int:
        return 1

    def inherit(
        self,
        parent_genomes: tuple[Genome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        del parent_genomes, genetic_architecture, rng
        raise AssertionError("Reproduction must use propagate(), not inherit().")

    def propagate(
        self,
        source_states: tuple[Genome, ...],
        *,
        recipient: object,
        context: GeneticArchitecture,
        rng: random.Random,
    ) -> Genome:
        del recipient, rng
        assert len(source_states) == 1
        context.validate_genome(source_states[0])
        return source_states[0]


def test_biological_production_builds_but_does_not_insert_offspring() -> None:
    """Test production constructs a newborn independently of world insertion."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    parent = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        x=4,
        y=6,
    )
    production = BiologicalOffspringProduction(
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=2),
    )

    offspring = production.produce(
        parent.transmissible_state,
        source_entities=(parent,),
        context=OffspringProductionContext(
            simulation_state=state,
            initial_energy=7,
        ),
        rng=state.rng,
    )

    assert offspring.genome == parent.genome
    assert offspring.energy == 7
    assert offspring.body_mass == 2
    assert (offspring.x, offspring.y) == (4, 6)
    assert len(state.domain_state.organisms) == 1
    with pytest.raises(RuntimeError):
        _ = offspring.id


def test_reproduction_uses_generic_propagation_before_entity_production() -> None:
    """Test reproduction composes propagation with separate entity production."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(genetic_architecture=architecture)
    parent = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=PropagationOnlyInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )

    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )

    assert event.offspring.genome == parent.genome
    assert event.offspring.energy == 5
    assert len(state.domain_state.organisms) == 1

    process.apply_event(state, event)

    assert len(state.domain_state.organisms) == 2
    assert state.domain_state.organisms[1] is event.offspring
