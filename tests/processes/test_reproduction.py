"""Tests for the Reproduction process."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    ClonalInheritance,
    SexualInheritance,
)
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    PairwiseMating,
    RandomParentLocation,
    SingleParent,
)
from evo_engine.spatial.neighborhoods import SameCell
from tests.helpers import (
    add_organism,
    make_integer_architecture,
    make_state,
)


def test_reproduction_rejects_parent_count_mismatch() -> None:
    """Test parent selection and inheritance must agree on arity."""
    with pytest.raises(ValueError):
        Reproduction(
            eligibility=AlwaysEligible(),
            parent_selection=SingleParent(),
            inheritance_model=SexualInheritance(),
            parental_investment=FixedEnergyInvestment(
                amount=5,
            ),
        )


def test_one_parent_proposal_records_energy_contribution() -> None:
    """Test clonal proposal captures the parent's committed investment."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(
        genetic_architecture=architecture,
    )
    parent = add_organism(
        state,
        trait_values={"offspring_energy": 10},
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=6,
        ),
    )

    proposals = process.propose_events(state)

    assert proposals == [
        Reproduction.Proposal(
            step_index=0,
            parent_energy_contributions=((parent.id, 6),),
        )
    ]


def test_proposal_omits_parent_group_that_cannot_afford_investment() -> None:
    """Test affordability before proposals enter resolution."""
    state = make_state()
    add_organism(
        state,
        energy=4,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )

    assert process.propose_events(state) == []


def test_proposal_rejects_zero_total_parental_investment() -> None:
    """Test every proposed offspring has positive starting energy."""
    state = make_state()
    add_organism(state)
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=0,
        ),
    )

    with pytest.raises(ValueError):
        process.propose_events(state)


def test_materialize_clonal_event_produces_genome_phenotype_and_location() -> None:
    """Test post-resolution materialization of a one-parent birth."""
    architecture = make_integer_architecture(
        "adult_body_mass",
        "offspring_energy",
    )
    state = make_state(
        genetic_architecture=architecture,
    )
    parent = add_organism(
        state,
        trait_values={
            "adult_body_mass": 8,
            "offspring_energy": 5,
        },
        energy=20,
        x=3,
        y=4,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_placement=RandomParentLocation(),
    )
    proposal = process.propose_events(state)[0]

    event = process.materialize_event(
        state,
        proposal,
    )

    assert event.parent_ids == (parent.id,)
    assert event.initial_energy == 5
    assert event.offspring_genetic_phenotype["adult_body_mass"] == 8
    assert (event.x, event.y) == (3, 4)


def test_apply_event_is_mechanical_and_does_not_advance_rng() -> None:
    """Test application performs no deferred stochastic decisions."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(
        genetic_architecture=architecture,
        seed=10,
    )
    parent = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )
    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )
    expected_rng = random.Random()
    expected_rng.setstate(state.rng.getstate())

    process.apply_event(
        state,
        event,
    )

    assert state.rng.random() == expected_rng.random()
    assert parent.energy == 15
    assert state.domain_state.organisms[1].energy == 5


def test_materialize_rechecks_recorded_parent_affordability() -> None:
    """Test stale resolved proposals cannot overdraw parent energy."""
    state = make_state()
    parent = add_organism(
        state,
        energy=10,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=8,
        ),
    )
    proposal = process.propose_events(state)[0]
    parent.energy = 3

    with pytest.raises(RuntimeError):
        process.materialize_event(
            state,
            proposal,
        )


def test_apply_rechecks_parent_affordability_atomically() -> None:
    """Test failed application does not partially charge parents."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(
        genetic_architecture=architecture,
    )
    first = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=10,
    )
    second = add_organism(
        state,
        trait_values={"offspring_energy": 5},
        energy=10,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=PairwiseMating(
            neighborhood=SameCell(),
        ),
        inheritance_model=SexualInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )
    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )
    second.energy = 2

    with pytest.raises(RuntimeError):
        process.apply_event(
            state,
            event,
        )

    assert first.energy == 10
    assert second.energy == 2
    assert len(state.domain_state.organisms) == 2


def test_two_parent_materialization_uses_sexual_inheritance() -> None:
    """Test two resolved parents contribute one haploid gamete each."""
    architecture = make_integer_architecture("offspring_energy")
    state = make_state(
        genetic_architecture=architecture,
        seed=4,
    )
    first = add_organism(
        state,
        trait_values={"offspring_energy": 10},
        energy=20,
    )
    second = add_organism(
        state,
        trait_values={"offspring_energy": 20},
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=PairwiseMating(
            neighborhood=SameCell(),
        ),
        inheritance_model=SexualInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )

    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )

    inherited_values = tuple(
        allele.value for allele in event.offspring_genome.alleles_at("offspring_energy")
    )

    assert len(inherited_values) == 2
    assert inherited_values[0] == 10
    assert inherited_values[1] == 20
    assert set(event.parent_ids) == {
        first.id,
        second.id,
    }


def test_default_reproduction_materializes_current_mass_from_adult_target() -> None:
    """Test newborn current mass is decided during materialization."""
    architecture = make_integer_architecture(
        "adult_body_mass",
        "offspring_energy",
    )
    state = make_state(
        genetic_architecture=architecture,
    )
    add_organism(
        state,
        trait_values={
            "adult_body_mass": 7,
            "offspring_energy": 5,
        },
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
    )

    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )

    assert event.initial_body_mass == 7

    process.apply_event(state, event)

    assert state.domain_state.organisms[1].body_mass == 7


def test_reproduction_declares_only_configured_policy_trait_dependencies() -> None:
    """Test trait requirements emerge from the chosen reproduction policies."""
    from evo_engine.genetics import ADULT_BODY_MASS, OFFSPRING_ENERGY
    from evo_engine.reproduction import GeneticPhenotypeEnergyInvestment

    default_process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=GeneticPhenotypeEnergyInvestment(),
    )
    fixed_process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )

    assert default_process.required_traits == frozenset(
        {
            ADULT_BODY_MASS,
            OFFSPRING_ENERGY,
        }
    )
    assert fixed_process.required_traits == frozenset()


def test_reproduction_materializes_development_after_genetic_expression() -> None:
    """Test offspring development varies around the inherited genetic value."""
    from evo_engine.development import (
        GaussianIntegerDevelopment,
        IndependentDevelopment,
    )
    from evo_engine.genetics import ADULT_BODY_MASS
    from evo_engine.reproduction import FractionOfAdultBodyMassAtBirth

    architecture = make_integer_architecture(
        ADULT_BODY_MASS,
        "offspring_energy",
    )
    state = make_state(
        genetic_architecture=architecture,
        seed=1,
    )
    add_organism(
        state,
        trait_values={
            ADULT_BODY_MASS: 20,
            "offspring_energy": 5,
        },
        energy=20,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        development_model=IndependentDevelopment(
            trait_models=(
                (
                    ADULT_BODY_MASS,
                    GaussianIntegerDevelopment(
                        standard_deviation=2,
                        minimum=1,
                    ),
                ),
            ),
        ),
        offspring_body_mass_model=FractionOfAdultBodyMassAtBirth(
            numerator=1,
            denominator=2,
        ),
    )

    event = process.materialize_event(
        state,
        process.propose_events(state)[0],
    )

    assert event.offspring_genetic_phenotype[ADULT_BODY_MASS] == 20
    assert event.offspring_developmental_profile[ADULT_BODY_MASS] == 23
    assert event.initial_body_mass == 11

    process.apply_event(state, event)
    offspring = state.domain_state.organisms[1]

    assert offspring.genetic_phenotype[ADULT_BODY_MASS] == 20
    assert offspring.developmental_profile[ADULT_BODY_MASS] == 23
    assert offspring.body_mass == 11
