"""Tests for reusable predation eligibility and preference policies."""

from __future__ import annotations

import pytest

from evo_engine.genetics import ATTACK_STRENGTH, DEFENSE
from evo_engine.predation import (
    AllOfPredationEligibility,
    GeneticAttackAdvantagePreference,
    GeneticAttackDefenseEligibility,
    LargerPredatorEligibility,
    NeutralPredationPreference,
)
from tests.helpers import add_organism, make_integer_architecture, make_state


def make_combatants(
    *,
    predator_attack: int = 8,
    prey_defense: int = 5,
    predator_mass: int = 10,
    prey_mass: int = 6,
):
    """Return predator and prey with attack/defense traits."""
    architecture = make_integer_architecture(ATTACK_STRENGTH, DEFENSE)
    state = make_state(genetic_architecture=architecture)
    predator = add_organism(
        state,
        trait_values={ATTACK_STRENGTH: predator_attack, DEFENSE: 1},
        body_mass=predator_mass,
    )
    prey = add_organism(
        state,
        trait_values={ATTACK_STRENGTH: 1, DEFENSE: prey_defense},
        body_mass=prey_mass,
    )
    return state, predator, prey


def test_larger_predator_eligibility_uses_current_mass() -> None:
    """Test current body mass rather than adult target controls size eligibility."""
    state, predator, prey = make_combatants(predator_mass=4, prey_mass=6)

    assert not LargerPredatorEligibility()(predator, prey, state)
    assert LargerPredatorEligibility()(prey, predator, state)


def test_attack_defense_eligibility_requires_strict_attack_advantage() -> None:
    """Test attack must strictly exceed prey defense."""
    state, predator, prey = make_combatants(predator_attack=5, prey_defense=5)
    policy = GeneticAttackDefenseEligibility()

    assert not policy(predator, prey, state)


def test_attack_defense_eligibility_declares_both_traits() -> None:
    """Test predation performance participates in trait preflight."""
    assert GeneticAttackDefenseEligibility().required_traits == frozenset(
        {ATTACK_STRENGTH, DEFENSE}
    )


def test_all_of_predation_eligibility_requires_every_policy() -> None:
    """Test composed eligibility rejects a pairing when one condition fails."""
    state, predator, prey = make_combatants(
        predator_attack=8,
        prey_defense=5,
        predator_mass=4,
        prey_mass=6,
    )
    policy = AllOfPredationEligibility(
        eligibilities=(
            LargerPredatorEligibility(),
            GeneticAttackDefenseEligibility(),
        )
    )

    assert not policy(predator, prey, state)
    assert policy.required_traits == frozenset({ATTACK_STRENGTH, DEFENSE})


def test_all_of_predation_eligibility_rejects_empty_composition() -> None:
    """Test a composed predation rule cannot vacuously allow every pairing."""
    with pytest.raises(ValueError):
        AllOfPredationEligibility(eligibilities=())


def test_attack_advantage_preference_scores_genetic_margin() -> None:
    """Test higher predator attack and lower prey defense increase preference."""
    state, predator, prey = make_combatants(predator_attack=9, prey_defense=4)
    preference = GeneticAttackAdvantagePreference()

    assert preference(predator, prey, state) == 5
    assert preference.required_traits == frozenset({ATTACK_STRENGTH, DEFENSE})


def test_neutral_predation_preference_returns_zero() -> None:
    """Test the compatibility default preserves proposal-order tie breaking."""
    state, predator, prey = make_combatants()

    assert NeutralPredationPreference()(predator, prey, state) == 0
