"""Integration tests for environmental reproductive-identity development."""

from __future__ import annotations

import random

from evo_engine.behavior import UnrestrictedBehavior
from evo_engine.development import (
    EnvironmentalThresholdDevelopment,
    IndependentDevelopment,
    WorldMeanEnvironmentalSampling,
)
from evo_engine.engine import SimulationState
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
    DevelopmentalProfileMatingType,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from evo_engine.world import EnvironmentalField, Organism, WorldState


def test_environment_can_determine_offspring_mating_type_through_development() -> None:
    """Test environment changes developmental identity without changing genotype."""
    trait_name = "reproductive_identity"
    locus = Locus(
        name=trait_name,
        chromosome_name="1",
        position=0,
        domain=ChoiceAlleleDomain(values=("genetic_default",)),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        loci=(locus,),
        traits=(
            Trait(
                name=trait_name,
                locus_names=(trait_name,),
                expression=CompleteDominanceExpression(
                    dominance_order=("genetic_default",),
                ),
            ),
        ),
    )
    allele = locus.create_allele("genetic_default")
    genome = Genome(
        chromosomes=(
            Chromosome(name="1", alleles=(allele,)),
            Chromosome(name="1", alleles=(allele,)),
        )
    )
    world = WorldState(
        width=2,
        height=1,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=30),
        ),
    )
    state = SimulationState(
        domain_state=world,
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
        rng=random.Random(1),
    )
    parent = Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
        energy=20,
    )
    state.domain_state.add_organism(parent)
    development = IndependentDevelopment(
        trait_models=(
            (
                trait_name,
                EnvironmentalThresholdDevelopment(
                    environmental_field_name="temperature",
                    threshold=25,
                    below_value="type_a",
                    at_or_above_value="type_b",
                    sampling=WorldMeanEnvironmentalSampling(),
                ),
            ),
        )
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        reproductive_group_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        reproductive_energy_investment=FixedEnergyInvestment(amount=5),
        development_model=development,
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
        offspring_mating_type_model=DevelopmentalProfileMatingType(
            trait_name=trait_name
        ),
    )

    event = process.materialize_event(state, process.propose_events(state)[0])

    assert event.offspring_genetic_phenotype[trait_name] == "genetic_default"
    assert event.offspring_developmental_profile[trait_name] == "type_b"
    assert event.offspring_mating_type == "type_b"
