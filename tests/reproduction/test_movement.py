"""Tests for reproduction-aware movement policies."""

from __future__ import annotations

import pytest

from evo_engine.behavior import REPRODUCTION
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.reproduction import (
    AlwaysEligible,
    PreferredMateTarget,
    ReproductiveEligibilityMovementCondition,
)
from evo_engine.world.organism import Organism
from tests.helpers import add_organism, make_state


class _Compatibility:
    def __init__(self, decision: bool = True) -> None:
        self.decision = decision

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        return self.decision


class _InvalidCompatibility:
    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        return 1


class _PreferenceByCandidateId:
    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        return second_parent.id


class _FixedPreference:
    def __init__(self, score: int) -> None:
        self.score = score

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        return self.score


class _InvalidPreference:
    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        return True


class _AgeEligibility:
    required_traits = frozenset({"maturity_age"})

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        return organism.age >= 1


class _InvalidEligibility:
    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        return 1


def test_reproductive_eligibility_condition_adapts_eligibility_policy() -> None:
    """Test reproductive readiness can participate in movement priorities."""
    state = make_state()
    juvenile = add_organism(
        state,
        age=0,
    )
    adult = add_organism(
        state,
        age=1,
    )
    condition = ReproductiveEligibilityMovementCondition(
        eligibility=_AgeEligibility(),
    )

    assert not condition.matches(
        juvenile,
        simulation_state=state,
    )
    assert condition.matches(
        adult,
        simulation_state=state,
    )
    assert condition.required_traits == frozenset({"maturity_age"})


def test_reproductive_eligibility_condition_requires_exact_boolean() -> None:
    """Test malformed reproductive eligibility cannot leak into movement."""
    state = make_state()
    organism = add_organism(state)
    condition = ReproductiveEligibilityMovementCondition(
        eligibility=_InvalidEligibility(),  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError):
        condition.matches(
            organism,
            simulation_state=state,
        )


def test_preferred_mate_target_prefers_score_before_distance() -> None:
    """Test sexual preference can outweigh proximity during mate seeking."""
    state = make_state(
        width=10,
        height=10,
    )
    focal = add_organism(
        state,
        x=0,
        y=0,
    )
    add_organism(
        state,
        x=1,
        y=0,
    )
    preferred = add_organism(
        state,
        x=3,
        y=0,
    )
    target_model = PreferredMateTarget(
        eligibility=AlwaysEligible(),
        compatibility=_Compatibility(),
        preference=_PreferenceByCandidateId(),
    )

    target = target_model.choose_target(
        focal,
        behavioral_purpose=REPRODUCTION,
        simulation_state=state,
    )

    assert target is not None
    assert (target.x, target.y) == (preferred.x, preferred.y)


def test_preferred_mate_target_ignores_ineligible_candidates() -> None:
    """Test mate seeking only targets individually available partners."""
    state = make_state()
    focal = add_organism(
        state,
        age=1,
        x=0,
        y=0,
    )
    add_organism(
        state,
        age=0,
        x=1,
        y=0,
    )
    adult = add_organism(
        state,
        age=1,
        x=2,
        y=0,
    )
    target_model = PreferredMateTarget(
        eligibility=_AgeEligibility(),
        compatibility=_Compatibility(),
        preference=_PreferenceByCandidateId(),
    )

    target = target_model.choose_target(
        focal,
        behavioral_purpose=REPRODUCTION,
        simulation_state=state,
    )

    assert target is not None
    assert (target.x, target.y) == (adult.x, adult.y)


def test_preferred_mate_target_requires_reproductive_purpose() -> None:
    """Test the reproduction-domain target stays inactive for other motives."""
    state = make_state()
    focal = add_organism(state)
    add_organism(
        state,
        x=1,
        y=0,
    )
    target_model = PreferredMateTarget(
        eligibility=AlwaysEligible(),
        compatibility=_Compatibility(),
        preference=_PreferenceByCandidateId(),
    )

    assert (
        target_model.choose_target(
            focal,
            behavioral_purpose="exploration",
            simulation_state=state,
        )
        is None
    )


def test_preferred_mate_target_rejects_non_boolean_compatibility() -> None:
    """Test target selection validates compatibility return contracts."""
    state = make_state()
    focal = add_organism(state)
    add_organism(
        state,
        x=1,
        y=0,
    )
    target_model = PreferredMateTarget(
        eligibility=AlwaysEligible(),
        compatibility=_InvalidCompatibility(),  # type: ignore[arg-type]
        preference=_FixedPreference(0),
    )

    with pytest.raises(TypeError):
        target_model.choose_target(
            focal,
            behavioral_purpose=REPRODUCTION,
            simulation_state=state,
        )


def test_preferred_mate_target_rejects_non_integer_preference() -> None:
    """Test target selection validates preference return contracts."""
    state = make_state()
    focal = add_organism(state)
    add_organism(
        state,
        x=1,
        y=0,
    )
    target_model = PreferredMateTarget(
        eligibility=AlwaysEligible(),
        compatibility=_Compatibility(),
        preference=_InvalidPreference(),  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError):
        target_model.choose_target(
            focal,
            behavioral_purpose=REPRODUCTION,
            simulation_state=state,
        )
