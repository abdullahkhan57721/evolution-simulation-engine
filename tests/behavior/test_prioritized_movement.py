"""Tests for prioritized movement intent and purpose-routed targeting."""

from __future__ import annotations

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    REPRODUCTION,
    EnergyBelowThresholdMovementCondition,
    MovementIntentRule,
    MovementTarget,
    PrioritizedMovementIntent,
    PurposeMovementTargetRouter,
    PurposeTargetRoute,
    determine_movement_purpose,
    determine_movement_target,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world.organism import Organism
from tests.helpers import add_organism, make_state


class _FixedCondition:
    def __init__(self, decision: bool) -> None:
        self.decision = decision

    def matches(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        return self.decision


class _InvalidCondition:
    def matches(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        return 1


class _FixedTarget:
    def __init__(
        self,
        target: MovementTarget | None,
        *,
        required_traits: frozenset[str] = frozenset(),
    ) -> None:
        self.target = target
        self.required_traits = required_traits

    def choose_target(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> MovementTarget | None:
        return self.target


def test_energy_below_threshold_condition_uses_strict_boundary() -> None:
    """Test threshold equality is not considered low energy."""
    state = make_state()
    organism = add_organism(
        state,
        energy=9,
    )
    condition = EnergyBelowThresholdMovementCondition(
        energy_threshold=10,
    )

    assert condition.matches(
        organism,
        simulation_state=state,
    )

    organism.energy = 10

    assert not condition.matches(
        organism,
        simulation_state=state,
    )


def test_prioritized_movement_intent_selects_first_matching_rule() -> None:
    """Test ordered rules short-circuit at the highest-priority match."""
    state = make_state()
    organism = add_organism(state)
    model = PrioritizedMovementIntent(
        rules=(
            MovementIntentRule(
                behavioral_purpose=ENERGY_ACQUISITION,
                condition=_FixedCondition(True),
            ),
            MovementIntentRule(
                behavioral_purpose=REPRODUCTION,
                condition=_FixedCondition(True),
            ),
        ),
    )

    assert (
        determine_movement_purpose(
            model,
            organism,
            simulation_state=state,
        )
        == ENERGY_ACQUISITION
    )


def test_prioritized_movement_intent_uses_fallback_when_no_rule_matches() -> None:
    """Test fallback purpose applies only when no priority condition matches."""
    state = make_state()
    organism = add_organism(state)
    model = PrioritizedMovementIntent(
        rules=(
            MovementIntentRule(
                behavioral_purpose=REPRODUCTION,
                condition=_FixedCondition(False),
            ),
        ),
        fallback_purpose=EXPLORATION,
    )

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == EXPLORATION
    )


def test_prioritized_movement_intent_requires_exact_boolean_condition() -> None:
    """Test condition return contracts are validated at the intent boundary."""
    state = make_state()
    organism = add_organism(state)
    model = PrioritizedMovementIntent(
        rules=(
            MovementIntentRule(
                behavioral_purpose=REPRODUCTION,
                condition=_InvalidCondition(),  # type: ignore[arg-type]
            ),
        ),
    )

    with pytest.raises(TypeError):
        model.determine_purpose(
            organism,
            simulation_state=state,
        )


def test_purpose_target_router_dispatches_by_behavioral_purpose() -> None:
    """Test each movement purpose reaches only its configured target model."""
    state = make_state()
    organism = add_organism(state)
    router = PurposeMovementTargetRouter(
        routes=(
            PurposeTargetRoute(
                behavioral_purpose=ENERGY_ACQUISITION,
                target_model=_FixedTarget(
                    MovementTarget(
                        x=1,
                        y=2,
                    )
                ),
            ),
            PurposeTargetRoute(
                behavioral_purpose=REPRODUCTION,
                target_model=_FixedTarget(
                    MovementTarget(
                        x=3,
                        y=4,
                    )
                ),
            ),
        ),
    )

    assert determine_movement_target(
        router,
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=state,
    ) == MovementTarget(
        x=1,
        y=2,
    )
    assert determine_movement_target(
        router,
        organism,
        behavioral_purpose=REPRODUCTION,
        simulation_state=state,
    ) == MovementTarget(
        x=3,
        y=4,
    )
    assert (
        determine_movement_target(
            router,
            organism,
            behavioral_purpose=EXPLORATION,
            simulation_state=state,
        )
        is None
    )


def test_purpose_target_router_rejects_duplicate_purposes() -> None:
    """Test one purpose cannot ambiguously route to two target models."""
    with pytest.raises(ValueError):
        PurposeMovementTargetRouter(
            routes=(
                PurposeTargetRoute(
                    behavioral_purpose=REPRODUCTION,
                    target_model=_FixedTarget(None),
                ),
                PurposeTargetRoute(
                    behavioral_purpose=REPRODUCTION,
                    target_model=_FixedTarget(None),
                ),
            ),
        )


def test_purpose_target_router_aggregates_routed_trait_requirements() -> None:
    """Test engine preflight can see traits needed by all possible targets."""
    router = PurposeMovementTargetRouter(
        routes=(
            PurposeTargetRoute(
                behavioral_purpose=ENERGY_ACQUISITION,
                target_model=_FixedTarget(
                    None,
                    required_traits=frozenset({"sensory_range"}),
                ),
            ),
            PurposeTargetRoute(
                behavioral_purpose=REPRODUCTION,
                target_model=_FixedTarget(
                    None,
                    required_traits=frozenset({"mating_signal"}),
                ),
            ),
        ),
    )

    assert router.required_traits == frozenset(
        {
            "sensory_range",
            "mating_signal",
        }
    )
