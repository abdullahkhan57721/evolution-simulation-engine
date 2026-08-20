"""Tests for exclusive preference-order resolvers."""

from __future__ import annotations

import pytest

from evo_engine.processes import Predation, Reproduction
from evo_engine.resolvers.predation import PreferenceOrder as PredationPreferenceOrder
from evo_engine.resolvers.reproduction import (
    PreferenceOrder as ReproductionPreferenceOrder,
)
from tests.helpers import make_state


def predation_event(
    predator_id: int,
    prey_id: int,
    preference_score: int,
) -> Predation.Event:
    """Return a minimal predation event."""
    return Predation.Event(
        step_index=0,
        predator_id=predator_id,
        prey_id=prey_id,
        x=0,
        y=0,
        predator_energy_gain=1,
        carcass_resource_units=1,
        preference_score=preference_score,
    )


def reproduction_proposal(
    parent_ids: tuple[int, ...],
    preference_score: int,
) -> Reproduction.Proposal:
    """Return a minimal reproduction proposal."""
    return Reproduction.Proposal(
        step_index=0,
        parent_energy_contributions=tuple((parent_id, 1) for parent_id in parent_ids),
        preference_score=preference_score,
    )


def test_predation_resolver_prefers_highest_score() -> None:
    """Test greedy preference ordering."""
    state = make_state()
    low = predation_event(0, 1, 1)
    high = predation_event(0, 2, 5)

    resolved = PredationPreferenceOrder().resolve_events(
        state,
        [
            low,
            high,
        ],
    )

    assert resolved == [high]


def test_predation_resolver_blocks_chain_participation() -> None:
    """Test an organism cannot be prey in one event and predator in another."""
    state = make_state()
    first = predation_event(0, 1, 10)
    second = predation_event(1, 2, 9)

    resolved = PredationPreferenceOrder().resolve_events(
        state,
        [
            first,
            second,
        ],
    )

    assert resolved == [first]


def test_preference_ties_preserve_proposal_order() -> None:
    """Test deterministic greedy tie-breaking."""
    state = make_state()
    first = reproduction_proposal(
        (0, 1),
        5,
    )
    second = reproduction_proposal(
        (0, 2),
        5,
    )

    resolved = ReproductionPreferenceOrder().resolve_events(
        state,
        [
            first,
            second,
        ],
    )

    assert resolved == [first]


def test_reproduction_resolver_allows_disjoint_pairs() -> None:
    """Test compatible parent pairs may both reproduce."""
    state = make_state()
    first = reproduction_proposal(
        (0, 1),
        5,
    )
    second = reproduction_proposal(
        (2, 3),
        4,
    )

    resolved = ReproductionPreferenceOrder().resolve_events(
        state,
        [
            first,
            second,
        ],
    )

    assert resolved == [
        first,
        second,
    ]


def test_specialized_resolver_rejects_wrong_event_type() -> None:
    """Test resolver domains are type constrained."""
    state = make_state()

    with pytest.raises(TypeError):
        PredationPreferenceOrder().resolve_events(
            state,
            [
                reproduction_proposal(
                    (0,),
                    0,
                )
            ],
        )
