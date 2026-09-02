"""Integration tests for prioritized mate-seeking movement."""

from __future__ import annotations

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    REPRODUCTION,
    EnergyBelowThresholdMovementCondition,
    MovementIntentRule,
    PrioritizedMovementIntent,
    PurposeMovementTargetRouter,
    PurposeTargetRoute,
)
from evo_engine.energetics import FixedLocomotionCost
from evo_engine.engine import StageCoordinator
from evo_engine.genetics import (
    CHOOSINESS,
    MATE_SEARCH_RANGE,
    MATING_SIGNAL,
    MAX_SPEED,
    SexualInheritance,
)
from evo_engine.processes import Movement, Reproduction
from evo_engine.reproduction import (
    AllOfMatingCompatibility,
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    MutualMateSearchRange,
    MutualSignalCompatibility,
    MutualSignalMarginPreference,
    PairwiseMating,
    PreferredMateTarget,
    ReproductiveEligibilityMovementCondition,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.reproduction import PreferenceOrder
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import MooreRandom
from evo_engine.spatial.neighborhoods import Moore
from tests.helpers import add_organism, make_integer_architecture, make_state


def _mate_seeking_process():
    eligibility = AlwaysEligible()
    compatibility = AllOfMatingCompatibility(
        compatibilities=(
            MutualMateSearchRange(),
            MutualSignalCompatibility(),
        )
    )
    preference = MutualSignalMarginPreference()
    process = Movement(
        movement_pattern=MooreRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_intent_model=PrioritizedMovementIntent(
            rules=(
                MovementIntentRule(
                    behavioral_purpose=ENERGY_ACQUISITION,
                    condition=EnergyBelowThresholdMovementCondition(
                        energy_threshold=10,
                    ),
                ),
                MovementIntentRule(
                    behavioral_purpose=REPRODUCTION,
                    condition=ReproductiveEligibilityMovementCondition(
                        eligibility=eligibility,
                    ),
                ),
            ),
        ),
        movement_target_model=PurposeMovementTargetRouter(
            routes=(
                PurposeTargetRoute(
                    behavioral_purpose=REPRODUCTION,
                    target_model=PreferredMateTarget(
                        eligibility=eligibility,
                        compatibility=compatibility,
                        preference=preference,
                    ),
                ),
            ),
        ),
    )
    return process, eligibility, compatibility, preference


def test_low_energy_priority_overrides_mate_seeking() -> None:
    """Test survival-oriented acquisition outranks reproduction motivation."""
    architecture = make_integer_architecture(
        MAX_SPEED,
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
    )
    state = make_state(genetic_architecture=architecture)
    focal = add_organism(
        state,
        trait_values={
            MAX_SPEED: 1,
            MATE_SEARCH_RANGE: 3,
            CHOOSINESS: 5,
            MATING_SIGNAL: 8,
        },
        energy=5,
        x=0,
        y=0,
    )
    add_organism(
        state,
        trait_values={
            MAX_SPEED: 1,
            MATE_SEARCH_RANGE: 3,
            CHOOSINESS: 5,
            MATING_SIGNAL: 8,
        },
        energy=30,
        x=2,
        y=0,
    )
    process, _, _, _ = _mate_seeking_process()

    event = process.propose_events(state)[0]

    assert event.organism_id == focal.id
    assert event.behavioral_purpose == ENERGY_ACQUISITION
    assert event.target_x is None
    assert event.target_y is None


def test_mate_seeking_closes_distance_and_enables_reproduction() -> None:
    """Test adults approach viable mates and then reproduce at close range."""
    architecture = make_integer_architecture(
        MAX_SPEED,
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
    )
    state = make_state(width=6, height=3, genetic_architecture=architecture)
    trait_values = {
        MAX_SPEED: 1,
        MATE_SEARCH_RANGE: 3,
        CHOOSINESS: 5,
        MATING_SIGNAL: 8,
    }
    first = add_organism(
        state,
        trait_values=trait_values,
        energy=20,
        x=0,
        y=1,
    )
    second = add_organism(
        state,
        trait_values=trait_values,
        energy=20,
        x=2,
        y=1,
    )
    movement, eligibility, compatibility, preference = _mate_seeking_process()
    movement_stage = StageCoordinator(processes=(movement,), resolver=AcceptAll())

    movement_stage.coordinate(state)

    assert (first.x, first.y) == (1, 1)
    assert (second.x, second.y) == (1, 1)

    reproduction = Reproduction(
        eligibility=eligibility,
        reproductive_group_selection=PairwiseMating(
            neighborhood=Moore(radius=1),
            can_mate=compatibility,
            preference_function=preference,
        ),
        inheritance_model=SexualInheritance(),
        reproductive_energy_investment=FixedEnergyInvestment(amount=1),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )
    reproduction_stage = StageCoordinator(
        processes=(reproduction,),
        resolver=PreferenceOrder(),
    )

    reproduction_stage.coordinate(state)

    assert len(state.domain_state.organisms) == 3
    assert first.energy == 19
    assert second.energy == 19
