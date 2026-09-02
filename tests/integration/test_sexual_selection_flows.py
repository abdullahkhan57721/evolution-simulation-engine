"""Integration tests for trait-driven mate choice and sexual selection."""

from __future__ import annotations

from evo_engine.engine import StageCoordinator
from evo_engine.genetics import (
    CHOOSINESS,
    MATE_SEARCH_RANGE,
    MATING_SIGNAL,
    SexualInheritance,
)
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    MutualMateSearchRange,
    MutualSignalCompatibility,
    MutualSignalMarginPreference,
    PairwiseMating,
)
from evo_engine.resolvers.reproduction import PreferenceOrder
from evo_engine.spatial.neighborhoods import Moore
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_sexual_selection_changes_which_compatible_pair_reproduces() -> None:
    """Test mating-signal preference drives resolved reproductive competition."""
    architecture = make_integer_architecture(
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
    )
    state = make_state(
        width=5,
        height=5,
        genetic_architecture=architecture,
        seed=7,
    )
    strongest = add_organism(
        state,
        trait_values={
            MATE_SEARCH_RANGE: 5,
            CHOOSINESS: 5,
            MATING_SIGNAL: 10,
        },
        energy=10,
        x=0,
        y=0,
    )
    middle = add_organism(
        state,
        trait_values={
            MATE_SEARCH_RANGE: 5,
            CHOOSINESS: 5,
            MATING_SIGNAL: 8,
        },
        energy=10,
        x=1,
        y=0,
    )
    weakest = add_organism(
        state,
        trait_values={
            MATE_SEARCH_RANGE: 5,
            CHOOSINESS: 5,
            MATING_SIGNAL: 6,
        },
        energy=10,
        x=2,
        y=0,
    )
    stage = StageCoordinator(
        processes=(
            Reproduction(
                eligibility=AlwaysEligible(),
                reproductive_group_selection=PairwiseMating(
                    neighborhood=Moore(radius=5),
                    can_mate=AllOfMatingCompatibility(
                        compatibilities=(
                            MutualMateSearchRange(),
                            MutualSignalCompatibility(),
                        )
                    ),
                    preference_function=MutualSignalMarginPreference(),
                ),
                inheritance_model=SexualInheritance(),
                parental_investment=FixedEnergyInvestment(amount=1),
                offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
            ),
        ),
        resolver=PreferenceOrder(),
    )

    stage.coordinate(state)

    assert strongest.energy == 9
    assert middle.energy == 9
    assert weakest.energy == 10
    assert len(state.domain_state.organisms) == 4
    newborn = max(
        state.domain_state.organisms.values(),
        key=lambda organism: organism.id,
    )
    assert newborn.energy == 2
