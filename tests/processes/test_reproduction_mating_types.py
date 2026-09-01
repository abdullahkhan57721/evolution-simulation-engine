"""Tests for mating-type assignment in the Reproduction process."""

from __future__ import annotations

import random

from evo_engine.genetics import (
    ChoiceAlleleDomain,
    Chromosome,
    ClonalInheritance,
    CompleteDominanceExpression,
    GeneticArchitecture,
    Genome,
    Locus,
    NoMutation,
    Trait,
)
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    FixedMatingType,
    GeneticPhenotypeMatingType,
    OffspringMatingTypeModel,
    RandomMatingType,
    SingleParent,
)
from evo_engine.world import Organism
from tests.helpers import add_organism, make_state


def _process(*, mating_type_model: OffspringMatingTypeModel) -> Reproduction:
    return Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=5),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
        offspring_mating_type_model=mating_type_model,
    )


def test_materialized_event_records_and_applies_offspring_mating_type() -> None:
    """Test mating type is fully determined before mechanical application."""
    state = make_state()
    add_organism(state, energy=20, mating_type="parent")
    process = _process(mating_type_model=FixedMatingType(mating_type="offspring"))

    event = process.materialize_event(state, process.propose_events(state)[0])

    assert event.offspring_mating_type == "offspring"

    process.apply_event(state, event)

    assert state.domain_state.organisms[1].mating_type == "offspring"


def test_materialization_can_assign_mating_type_from_offspring_genetics() -> None:
    """Test Reproduction passes inherited offspring state to assignment policy."""
    trait_name = "reproductive_identity"
    locus = Locus(
        name=trait_name,
        chromosome_name="1",
        position=0,
        domain=ChoiceAlleleDomain(values=("alpha", "beta")),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        loci=(locus,),
        traits=(
            Trait(
                name=trait_name,
                locus_names=(trait_name,),
                expression=CompleteDominanceExpression(
                    dominance_order=("alpha", "beta"),
                ),
            ),
        ),
    )
    alpha_allele = locus.create_allele("alpha")
    genome = Genome(
        chromosomes=(
            Chromosome(name="1", alleles=(alpha_allele,)),
            Chromosome(name="1", alleles=(alpha_allele,)),
        )
    )
    state = make_state(genetic_architecture=architecture)
    parent = Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
        energy=20,
        mating_type="parent",
    )
    state.domain_state.add_organism(parent)
    process = _process(
        mating_type_model=GeneticPhenotypeMatingType(trait_name=trait_name)
    )

    event = process.materialize_event(state, process.propose_events(state)[0])

    assert event.offspring_genetic_phenotype[trait_name] == "alpha"
    assert event.offspring_mating_type == "alpha"
    assert process.required_traits == frozenset({trait_name})


def test_proposals_do_not_consume_offspring_mating_type_rng() -> None:
    """Test rejected candidate proposals cannot consume assignment randomness."""
    state = make_state(seed=31)
    add_organism(state, energy=20)
    process = _process(
        mating_type_model=RandomMatingType(mating_types=("alpha", "beta"))
    )
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())

    proposals = process.propose_events(state)

    assert len(proposals) == 1
    assert state.rng.random() == expected_rng.random()


def test_application_does_not_advance_mating_type_rng() -> None:
    """Test stochastic mating-type choice is completed during materialization."""
    state = make_state(seed=43)
    add_organism(state, energy=20)
    process = _process(
        mating_type_model=RandomMatingType(mating_types=("alpha", "beta"))
    )
    event = process.materialize_event(state, process.propose_events(state)[0])
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())

    process.apply_event(state, event)

    assert state.rng.random() == expected_rng.random()
