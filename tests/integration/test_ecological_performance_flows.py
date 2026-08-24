"""Integration tests for sensory and predation performance traits."""

from __future__ import annotations

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    FixedSensoryRange,
    GeneticPhenotypeSensoryAccuracy,
    MovementTarget,
    NearestResourceTarget,
)
from evo_engine.engine import StageCoordinator
from evo_engine.genetics import ATTACK_STRENGTH, DEFENSE, SENSORY_ACCURACY
from evo_engine.predation import (
    AllOfPredationEligibility,
    GeneticAttackAdvantagePreference,
    GeneticAttackDefenseEligibility,
    LargerPredatorEligibility,
)
from evo_engine.processes import Predation
from evo_engine.resolvers.predation import PreferenceOrder
from evo_engine.spatial.neighborhoods import SameCell
from tests.helpers import add_organism, make_integer_architecture, make_state


def test_genetic_sensory_accuracy_changes_resource_detection() -> None:
    """Test expressed accuracy changes which in-range resources are perceived."""
    architecture = make_integer_architecture(SENSORY_ACCURACY)
    state = make_state(genetic_architecture=architecture)
    blind = add_organism(
        state,
        trait_values={SENSORY_ACCURACY: 0},
        x=1,
        y=1,
    )
    perfect = add_organism(
        state,
        trait_values={SENSORY_ACCURACY: 100},
        x=1,
        y=1,
    )
    state.world.add_resources(x=2, y=1, amount=5)
    model = NearestResourceTarget(
        sensory_range_model=FixedSensoryRange(radius=2),
        sensory_accuracy_model=GeneticPhenotypeSensoryAccuracy(),
    )

    assert (
        model.choose_target(
            blind,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=state,
        )
        is None
    )
    assert model.choose_target(
        perfect,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=state,
    ) == MovementTarget(x=2, y=1)


def test_attack_defense_advantage_controls_resolved_predation() -> None:
    """Test performance traits shape feasibility and prey choice in one stage."""
    architecture = make_integer_architecture(ATTACK_STRENGTH, DEFENSE)
    state = make_state(genetic_architecture=architecture)
    predator = add_organism(
        state,
        trait_values={ATTACK_STRENGTH: 10, DEFENSE: 2},
        body_mass=10,
        x=1,
        y=1,
    )
    vulnerable_prey = add_organism(
        state,
        trait_values={ATTACK_STRENGTH: 1, DEFENSE: 3},
        body_mass=5,
        x=1,
        y=1,
    )
    defended_prey = add_organism(
        state,
        trait_values={ATTACK_STRENGTH: 1, DEFENSE: 8},
        body_mass=5,
        x=1,
        y=1,
    )
    stage = StageCoordinator(
        processes=(
            Predation(
                neighborhood=SameCell(),
                consumption_percent=100,
                can_predate=AllOfPredationEligibility(
                    eligibilities=(
                        LargerPredatorEligibility(),
                        GeneticAttackDefenseEligibility(),
                    )
                ),
                preference_function=GeneticAttackAdvantagePreference(),
            ),
        ),
        resolver=PreferenceOrder(),
    )

    stage.coordinate(state)

    assert predator.id in state.world.organisms
    assert vulnerable_prey.id not in state.world.organisms
    assert defended_prey.id in state.world.organisms
    assert predator.energy == 105
